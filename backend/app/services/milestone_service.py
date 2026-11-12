from datetime import datetime, timedelta, timezone
import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.core.config import settings

from app.models import (
    Project,
    User,
    UserRole,
    Agreement,
    AgreementVersion,
    Milestone,
    MilestoneAudit,
    Dispute,
    Notification,
)


ALLOWED_STATUSES = {
    "not_started",
    "in_progress",
    "submitted",
    "under_review",
    "revision_requested",
    "approved",
    "payment_pending",
    "paid",
    "disputed",
}


def now():
    return datetime.now(timezone.utc)


def get_milestone(db: Session, milestone_id: int):
    milestone = db.query(Milestone).filter(
        Milestone.id == milestone_id
    ).with_for_update().first()

    if not milestone:
        raise HTTPException(404, "Milestone not found.")

    return milestone


def verify_project_participant(milestone, user):
    project = milestone.project

    if user.id not in [project.client_id, project.freelancer_id]:
        raise HTTPException(403, "You are not a project participant.")

    return project


def verify_freelancer(milestone, user):
    project = verify_project_participant(milestone, user)

    if (
        user.role != UserRole.FREELANCER
        or project.freelancer_id != user.id
    ):
        raise HTTPException(403, "Only the assigned freelancer can perform this action.")

    return project


def verify_client(milestone, user):
    project = verify_project_participant(milestone, user)

    if (
        user.role != UserRole.CLIENT
        or project.client_id != user.id
    ):
        raise HTTPException(403, "Only the project client can perform this action.")

    return project


def record_milestone_audit(
    db,
    milestone,
    user,
    previous_status,
    new_status,
    description,
    details=None,
):
    db.add(
        MilestoneAudit(
            milestone_id=milestone.id,
            actor_user_id=user.id,
            previous_status=previous_status,
            new_status=new_status,
            description=description,
            details=details or {},
        )
    )


def create_milestones_from_agreement(
    db: Session,
    version: AgreementVersion,
    actor_user_id: int,
):
    agreement = (
        db.query(Agreement)
        .filter(Agreement.id == version.agreement_id)
        .with_for_update()
        .first()
    )

    if not agreement or agreement.active_version_id != version.id:
        raise HTTPException(409, "Agreement version is not active.")

    expected_items = version.agreement_data.get("milestones", [])
    existing_version = (
        db.query(Milestone)
        .filter(Milestone.agreement_version_id == version.id)
        .all()
    )

    if len(existing_version) == len(expected_items):
        return existing_version
    if existing_version:
        # A prior interrupted/manual partial write is repaired by matching
        # immutable milestone attributes and adding only missing records.
        existing_keys = {}
        for row in existing_version:
            key = (row.title, str(row.amount), row.currency, row.description)
            existing_keys[key] = existing_keys.get(key, 0) + 1
    else:
        existing_keys = {}

    old_milestones = (
        db.query(Milestone)
        .filter(
            Milestone.project_id == agreement.project_id,
            Milestone.is_current.is_(True),
        )
        .with_for_update()
        .all()
    )

    for old in old_milestones:
        if old.agreement_version_id != version.id:
            old.is_current = False

    created = []

    for item in expected_items:
        item_key = (item["title"], str(item["amount"]), item["currency"], item["description"])
        if existing_keys.get(item_key, 0):
            existing_keys[item_key] -= 1
            continue
        due_date = item.get("due_date")

        if isinstance(due_date, str):
            due_date = datetime.fromisoformat(
                due_date.replace("Z", "+00:00")
            )

        milestone = Milestone(
            project_id=agreement.project_id,
            agreement_version_id=version.id,
            is_current=True,
            title=item["title"],
            description=item["description"],
            amount=item["amount"],
            currency=item["currency"],
            due_date=due_date,
            status="not_started",
            progress_percentage=0,
            deliverables=item["deliverables"],
            completion_criteria=item["completion_criteria"],
            review_period_days=item["review_period_days"],
        )

        db.add(milestone)
        db.flush()

        actor = db.get(User, actor_user_id)

        record_milestone_audit(
            db,
            milestone,
            actor,
            None,
            "not_started",
            "Milestone created from an approved agreement version.",
            {"agreement_version_id": version.id},
        )

        created.append(milestone)

    db.commit()

    return created


def update_milestone_progress(
    db: Session,
    milestone_id: int,
    user: User,
    progress: int,
):
    milestone = get_milestone(db, milestone_id)
    verify_freelancer(milestone, user)

    if milestone.status not in [
        "not_started",
        "in_progress",
        "revision_requested",
    ]:
        raise HTTPException(409, "Progress cannot be changed in this status.")

    previous = milestone.status

    milestone.progress_percentage = progress

    if progress > 0:
        milestone.status = "in_progress"

    record_milestone_audit(
        db,
        milestone,
        user,
        previous,
        milestone.status,
        "Milestone progress updated.",
        {"progress_percentage": progress},
    )

    db.commit()
    db.refresh(milestone)

    return milestone


def submit_milestone(
    db: Session,
    milestone_id: int,
    user: User,
    submission_url: str,
    submission_notes: str,
):
    milestone = get_milestone(db, milestone_id)
    verify_freelancer(milestone, user)

    if milestone.status not in [
        "in_progress",
        "revision_requested",
    ]:
        raise HTTPException(
            409,
            "This milestone cannot be submitted in its current status.",
        )

    previous = milestone.status
    submitted_at = now()

    milestone.submission_url = submission_url
    milestone.submission_notes = submission_notes
    milestone.submitted_at = submitted_at
    review_window = (timedelta(minutes=settings.MILESTONE_REVIEW_MINUTES)
                     if settings.MILESTONE_REVIEW_MINUTES > 0
                     else timedelta(hours=settings.MILESTONE_REVIEW_HOURS))
    milestone.review_deadline = submitted_at + review_window
    milestone.status = "submitted"
    milestone.progress_percentage = 100

    record_milestone_audit(
        db,
        milestone,
        user,
        previous,
        "submitted",
        "Freelancer submitted milestone work.",
        {"submission_url": submission_url},
    )
    project = milestone.project
    db.add(Notification(user_id=project.client_id, title="Milestone submitted for review", message=f"'{milestone.title}' has been submitted. Review it or raise a dispute before {milestone.review_deadline.isoformat()}.") )

    db.commit()
    db.refresh(milestone)

    # Persisted Celery jobs send reminders; the periodic sweep recovers missed jobs.
    try:
        from app.tasks.milestones import send_review_reminder, auto_approve_milestone
        if settings.MILESTONE_REMINDER_MINUTES.strip():
            reminder_offsets = [int(value.strip()) for value in settings.MILESTONE_REMINDER_MINUTES.split(",") if value.strip()]
        else:
            reminder_offsets = [int(value.strip()) * 60 for value in settings.MILESTONE_REMINDER_HOURS.split(",") if value.strip()]
        review_minutes = settings.MILESTONE_REVIEW_MINUTES or settings.MILESTONE_REVIEW_HOURS * 60
        auto_approve_milestone.apply_async(
            args=[milestone.id, milestone.submitted_at.isoformat()],
            countdown=review_minutes * 60,
            task_id=f"milestone-auto-approve-{milestone.id}-{int(milestone.submitted_at.timestamp())}",
        )
        for offset_minutes in reminder_offsets:
            if 0 < offset_minutes < review_minutes:
                send_review_reminder.apply_async(
                    args=[milestone.id, milestone.submitted_at.isoformat(), offset_minutes],
                    countdown=offset_minutes * 60,
                )
    except Exception:
        # The persisted periodic Celery sweep recovers reminders after Redis returns.
        logging.exception("Could not enqueue milestone reminder tasks; submission remains saved.")

    return milestone


def start_milestone_review(
    db: Session,
    milestone_id: int,
    user: User,
):
    milestone = get_milestone(db, milestone_id)
    verify_client(milestone, user)

    if milestone.status != "submitted":
        raise HTTPException(409, "Milestone is not awaiting review.")

    previous = milestone.status
    milestone.status = "under_review"

    record_milestone_audit(
        db, milestone, user, previous, "under_review",
        "Client started reviewing submitted work.",
    )

    db.commit()
    db.refresh(milestone)

    return milestone


def review_milestone(
    db: Session,
    milestone_id: int,
    user: User,
    action: str,
    explanation: str | None,
):
    milestone = get_milestone(db, milestone_id)
    verify_client(milestone, user)

    if milestone.status not in ["submitted", "under_review"]:
        raise HTTPException(409, "Milestone is not awaiting client review.")

    previous = milestone.status

    if action == "approve":
        milestone.status = "approved"
        milestone.approved_at = now()
        milestone.revision_explanation = None

    elif action == "request_revision":
        if not explanation or len(explanation.strip()) < 10:
            raise HTTPException(
                422,
                "Provide a clear explanation for the requested revision.",
            )

        milestone.status = "revision_requested"
        milestone.revision_explanation = explanation

    else:
        raise HTTPException(422, "Invalid review action.")

    record_milestone_audit(
        db,
        milestone,
        user,
        previous,
        milestone.status,
        "Client reviewed submitted milestone work.",
        {"action": action, "explanation": explanation},
    )
    project = milestone.project
    freelancer_message = (f"'{milestone.title}' was approved by the client." if action == "approve" else f"A revision was requested for '{milestone.title}': {explanation}")
    db.add(Notification(user_id=project.freelancer_id, title="Milestone review update", message=freelancer_message))

    db.commit()
    db.refresh(milestone)

    return milestone


def raise_milestone_dispute(
    db: Session,
    milestone_id: int,
    user: User,
    explanation: str,
):
    milestone = get_milestone(db, milestone_id)
    verify_project_participant(milestone, user)

    if milestone.status in ["paid", "disputed"]:
        raise HTTPException(
            409,
            "A dispute cannot be raised in the current milestone status.",
        )

    if len(explanation.strip()) < 20:
        raise HTTPException(
            422,
            "Provide at least 20 characters explaining the dispute.",
        )

    previous = milestone.status
    milestone.status = "disputed"

    dispute = Dispute(
        project_id=milestone.project_id,
        milestone_id=milestone.id,
        raised_by=user.id,
        reason=explanation.strip(),
        status="open",
    )
    db.add(dispute)
    db.flush()
    record_milestone_audit(
        db,
        milestone,
        user,
        previous,
        "disputed",
        "A project participant raised a milestone dispute.",
        {"explanation": explanation, "dispute_id": dispute.id},
    )
    project = milestone.project
    other_id = project.freelancer_id if user.id == project.client_id else project.client_id
    db.add(Notification(user_id=other_id, title="A milestone dispute was opened", message=f"A dispute was opened for '{milestone.title}'. Add evidence through the project workspace."))
    db.commit()
    db.refresh(milestone)
    return milestone

    return milestone