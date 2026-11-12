from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import (
    Project,
    User,
    UserRole,
    AIScopeVersion,
    Agreement,
    AgreementVersion,
    AgreementAudit,
    Notification,
    Milestone,
    PayPalPayment,
)
from app.schemas.agreement import AgreementData


def utc_now():
    return datetime.now(timezone.utc)


def get_project_participants(db: Session, project: Project):
    client = db.query(User).filter(
        User.id == project.client_id
    ).first()

    freelancer = None

    if project.freelancer_id:
        freelancer = db.query(User).filter(
            User.id == project.freelancer_id
        ).first()

    if not client or not freelancer:
        raise HTTPException(
            status_code=400,
            detail="The project must have both a client and an assigned freelancer.",
        )

    return client, freelancer


def get_approved_scope(db: Session, project_id: int):
    scope = (
        db.query(AIScopeVersion)
        .filter(
            AIScopeVersion.project_id == project_id,
            AIScopeVersion.is_approved.is_(True),
            AIScopeVersion.status == "approved",
        )
        .order_by(AIScopeVersion.version_number.desc())
        .first()
    )

    if not scope:
        raise HTTPException(
            status_code=400,
            detail="An approved AI project scope is required.",
        )

    return scope


def build_agreement_data(project, client, freelancer, scope_data):
    milestones = []

    for item in scope_data["milestones"]:
        milestones.append({
            "title": item["title"],
            "description": item["description"],
            "amount": item["amount"],
            "currency": project.currency,
            "due_date": item.get("suggested_submission_date"),
            "deliverables": item["deliverables"],
            "completion_criteria": item["completion_criteria"],
            "review_period_days": item["review_period_days"],
        })

    agreement_data = {
        "client_details": {
            "user_id": client.id,
            "full_name": client.full_name,
            "email": client.email,
            "role": client.role.value,
        },
        "freelancer_details": {
            "user_id": freelancer.id,
            "full_name": freelancer.full_name,
            "email": freelancer.email,
            "role": freelancer.role.value,
        },
        "project_title": project.title,
        "project_description": project.description,
        "deliverables": scope_data["deliverables"],
        "milestones": milestones,
        "total_budget": str(project.budget),
        "currency": project.currency,
        "estimated_duration_days": scope_data["estimated_duration_days"],
        "revision_limits": scope_data["revision_limits"],
        "acceptance_criteria": scope_data["acceptance_criteria"],
        "client_responsibilities": scope_data["client_responsibilities"],
        "freelancer_responsibilities": scope_data["freelancer_responsibilities"],
        "cancellation_terms": (
            "Cancellation must be requested through Aurevo. "
            "Completed and approved work remains subject to the agreed "
            "payment conditions and applicable dispute process."
        ),
        "dispute_procedure": (
            "Either party may raise a dispute through Aurevo. "
            "Both parties may provide supporting evidence. AI-generated "
            "recommendations are advisory and do not determine the outcome."
        ),
        "payment_conditions": (
            "Payments are processed according to the approved milestone "
            "amounts and the platform's payment workflow. A milestone "
            "approval is not itself confirmation of a successful payment."
        ),
    }

    validated = AgreementData.model_validate(agreement_data)

    total = sum(
        (item.amount for item in validated.milestones),
        Decimal("0"),
    )

    if total != validated.total_budget:
        raise HTTPException(
            status_code=422,
            detail="Agreement milestone amounts must equal the project budget.",
        )

    return validated.model_dump(mode="json")


def create_audit(
    db: Session,
    agreement_id: int,
    version_id: int | None,
    actor_user_id: int | None,
    action: str,
    description: str,
    details: dict | None = None,
):
    audit = AgreementAudit(
        agreement_id=agreement_id,
        version_id=version_id,
        actor_user_id=actor_user_id,
        action=action,
        description=description,
        details=details or {},
    )

    db.add(audit)


def generate_initial_agreement(
    db: Session,
    project_id: int,
    current_user: User,
):
    project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .with_for_update()
        .first()
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    if current_user.role != UserRole.CLIENT:
        raise HTTPException(
            status_code=403,
            detail="Only the client can generate the agreement.",
        )

    if project.client_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You do not own this project.",
        )

    existing = (
        db.query(Agreement)
        .filter(Agreement.project_id == project_id)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="An agreement already exists. Create a new version instead.",
        )

    scope = get_approved_scope(db, project_id)

    client, freelancer = get_project_participants(db, project)

    agreement_data = build_agreement_data(
        project,
        client,
        freelancer,
        scope.scope_data,
    )

    agreement = Agreement(
        project_id=project.id,
        status="pending",
    )

    db.add(agreement)
    db.flush()

    version = AgreementVersion(
        agreement_id=agreement.id,
        version_number=1,
        agreement_data=agreement_data,
        changed_fields=list(agreement_data.keys()),
        change_summary="Initial agreement generated from the approved project scope.",
        created_by=current_user.id,
        client_approved=False,
        freelancer_approved=False,
        status="pending_approval",
    )

    db.add(version)
    db.flush()
    db.add(Notification(user_id=freelancer.id, title="Agreement ready for approval", message=f"The client generated agreement v{version.version_number} for '{project.title}'. Review and approve it in the project workspace."))

    create_audit(
        db,
        agreement.id,
        version.id,
        current_user.id,
        "agreement_generated",
        "Initial agreement generated.",
        {"version_number": 1},
    )

    db.commit()
    db.refresh(version)

    return version


def find_changed_fields(old_data: dict, new_data: dict):
    changed = []

    all_keys = set(old_data.keys()) | set(new_data.keys())

    for key in sorted(all_keys):
        if old_data.get(key) != new_data.get(key):
            changed.append(key)

    return changed


def create_agreement_version(
    db: Session,
    agreement_id: int,
    current_user: User,
    agreement_data: dict,
    change_summary: str,
):
    agreement = (
        db.query(Agreement)
        .filter(Agreement.id == agreement_id)
        .with_for_update()
        .first()
    )

    if not agreement:
        raise HTTPException(status_code=404, detail="Agreement not found.")

    project = (
        db.query(Project)
        .filter(Project.id == agreement.project_id)
        .first()
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    if current_user.id not in [
        project.client_id,
        project.freelancer_id,
    ]:
        raise HTTPException(
            status_code=403,
            detail="You are not a participant in this project.",
        )

    if current_user.role not in [
        UserRole.CLIENT,
        UserRole.FREELANCER,
    ]:
        raise HTTPException(status_code=403, detail="Invalid role.")

    current_milestones = db.query(Milestone).filter(
        Milestone.project_id == project.id,
        Milestone.is_current.is_(True),
    ).all()
    if any(m.status != "not_started" or (m.progress_percentage or 0) > 0 or m.submitted_at for m in current_milestones):
        raise HTTPException(
            status_code=409,
            detail="Agreement revisions are available before milestone work begins. A started or submitted milestone must be resolved under the current agreement first.",
        )
    active_payment = db.query(PayPalPayment).filter(
        PayPalPayment.project_id == project.id,
        PayPalPayment.payment_status.notin_(["FAILED", "VOIDED", "EXPIRED"]),
    ).first()
    if active_payment:
        raise HTTPException(
            status_code=409,
            detail="Agreement revisions are unavailable while any project payment is pending, authorized, captured, or requires reconciliation.",
        )

    validated = AgreementData.model_validate(agreement_data)

    total = sum(
        (item.amount for item in validated.milestones),
        Decimal("0"),
    )

    if validated.client_details.get("user_id") != project.client_id or validated.freelancer_details.get("user_id") != project.freelancer_id:
        raise HTTPException(status_code=422, detail="Agreement parties must remain the client and freelancer assigned to this project.")
    if validated.currency.upper() != project.currency.upper():
        raise HTTPException(status_code=422, detail="Agreement currency must match the project's selected currency.")
    if any(item.currency.upper() != project.currency.upper() for item in validated.milestones):
        raise HTTPException(status_code=422, detail="Every milestone must use the project's selected currency.")
    if validated.total_budget != Decimal(str(project.budget)):
        raise HTTPException(status_code=422, detail="Agreement total budget must match the project budget.")
    if total != validated.total_budget:
        raise HTTPException(status_code=422, detail="Milestone amounts must equal the agreement budget.")

    if not agreement.active_version_id:
        raise HTTPException(status_code=409, detail="The initial agreement must be mutually approved before proposing revisions.")

    pending_version = db.query(AgreementVersion).filter(
        AgreementVersion.agreement_id == agreement.id,
        AgreementVersion.status == "pending_approval",
    ).first()
    if pending_version:
        raise HTTPException(status_code=409, detail="A proposed agreement version is already awaiting approval.")

    previous = db.query(AgreementVersion).filter(
        AgreementVersion.id == agreement.active_version_id,
        AgreementVersion.status == "active",
    ).first()
    if not previous:
        raise HTTPException(status_code=409, detail="The active agreement version could not be verified.")

    new_data = validated.model_dump(mode="json")

    changed_fields = find_changed_fields(
        previous.agreement_data,
        new_data,
    )

    if not changed_fields:
        raise HTTPException(
            status_code=400,
            detail="No agreement changes were detected.",
        )

    next_number = previous.version_number + 1

    version = AgreementVersion(
        agreement_id=agreement.id,
        version_number=next_number,
        previous_version_id=previous.id,
        agreement_data=new_data,
        changed_fields=changed_fields,
        change_summary=change_summary,
        created_by=current_user.id,
        client_approved=False,
        freelancer_approved=False,
        status="pending_approval",
    )

    db.add(version)
    db.flush()
    other_id = project.freelancer_id if current_user.id == project.client_id else project.client_id
    db.add(Notification(user_id=other_id, title="Agreement version updated", message=f"A new agreement version for '{project.title}' is ready for review."))

    create_audit(
        db,
        agreement.id,
        version.id,
        current_user.id,
        "agreement_version_created",
        change_summary,
        {
            "previous_version": previous.version_number,
            "new_version": next_number,
            "changed_fields": changed_fields,
        },
    )

    db.commit()
    db.refresh(version)

    return version


def approve_agreement_version(
    db: Session,
    version_id: int,
    current_user: User,
):
    version = (
        db.query(AgreementVersion)
        .filter(AgreementVersion.id == version_id)
        .with_for_update()
        .first()
    )

    if not version:
        raise HTTPException(
            status_code=404,
            detail="Agreement version not found.",
        )

    agreement = (
        db.query(Agreement)
        .filter(Agreement.id == version.agreement_id)
        .with_for_update()
        .first()
    )

    project = (
        db.query(Project)
        .filter(Project.id == agreement.project_id)
        .first()
    )

    if current_user.id not in (project.client_id, project.freelancer_id):
        raise HTTPException(status_code=403, detail="You are not a participant in this project.")

    # Approval is idempotent. This is essential when activation committed but
    # the follow-up milestone creation transaction failed and must be retried.
    if version.status == "active" and version.client_approved and version.freelancer_approved:
        return version

    if version.status != "pending_approval":
        raise HTTPException(status_code=409, detail="This agreement version is no longer awaiting approval.")

    if current_user.id == project.client_id:
        if not version.client_approved:
            version.client_approved = True
            version.client_approved_at = utc_now()
            action = "client_approved"
        else:
            action = None
    else:
        if not version.freelancer_approved:
            version.freelancer_approved = True
            version.freelancer_approved_at = utc_now()
            action = "freelancer_approved"
        else:
            action = None

    if action:
        create_audit(
            db,
            agreement.id,
            version.id,
            current_user.id,
            action,
            f"Agreement version {version.version_number} approved.",
        )

    if version.client_approved and version.freelancer_approved:

        previous_active = (
            db.query(AgreementVersion)
            .filter(AgreementVersion.id == agreement.active_version_id)
            .first()
            if agreement.active_version_id
            else None
        )

        if previous_active:
            previous_active.status = "superseded"

        version.status = "active"
        agreement.active_version_id = version.id
        agreement.status = "active"

        create_audit(
            db,
            agreement.id,
            version.id,
            current_user.id,
            "agreement_activated",
            f"Agreement version {version.version_number} is now active.",
        )
        db.add(Notification(user_id=project.client_id, title="Agreement activated", message=f"Both participants approved agreement v{version.version_number} for '{project.title}'. Milestones are now available."))
        db.add(Notification(user_id=project.freelancer_id, title="Agreement activated", message=f"Both participants approved agreement v{version.version_number} for '{project.title}'. Milestones are now available."))
    else:
        other_id = project.freelancer_id if current_user.id == project.client_id else project.client_id
        db.add(Notification(user_id=other_id, title="Agreement approval recorded", message=f"One participant approved agreement v{version.version_number} for '{project.title}'. Your approval is still required."))

    db.commit()
    db.refresh(version)

    return version