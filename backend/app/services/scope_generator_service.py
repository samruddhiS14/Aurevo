
"""Rule-based project scope generation without external AI services."""

from datetime import date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation

from sqlalchemy.orm import Session

from app.models import Project, AIScopeVersion
from app.schemas.ai_scope import (
    ProjectScopeData,
    MilestoneRecommendation,
)
from app.services.scope_validation import reconcile_scope_data


def _to_datetime(value):
    """Convert supported project date values into datetime."""

    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    if isinstance(value, date):
        return datetime.combine(value, time.min)

    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    return None


def _to_string_list(values):
    """Normalize project lists into non-empty strings."""

    if not values:
        return []

    if isinstance(values, str):
        values = [values]

    result = []

    for value in values:
        if isinstance(value, str):
            cleaned = value.strip()
        elif isinstance(value, dict):
            cleaned = (
                value.get("title")
                or value.get("name")
                or value.get("deliverable")
                or value.get("description")
                or ""
            )
            cleaned = str(cleaned).strip()
        else:
            cleaned = str(value).strip()

        if cleaned and cleaned not in result:
            result.append(cleaned)

    return result


def _make_milestone_date(start_date, duration_days, fraction):
    """Calculate a suggested date within the project timeline."""

    if start_date is None:
        return None

    days = max(0, round(duration_days * fraction))

    return start_date + timedelta(days=days)


def generate_project_scope(
    db: Session,
    project: Project,
    user_id: int,
    additional_instructions: str | None = None,
):
    """
    Generate a structured project scope using deterministic templates.

    No Gemini API or external AI service is required.
    """

    # 1. Validate the project budget.
    try:
        budget = Decimal(str(project.budget)).quantize(
            Decimal("0.01")
        )
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(
            "A valid project budget is required before generating a scope."
        ) from exc

    if not budget.is_finite() or budget <= 0:
        raise ValueError(
            "A valid positive project budget is required."
        )

    if budget < Decimal("0.03"):
        raise ValueError(
            "The project budget is too small for three positive milestones."
        )

    currency = project.currency or "USD"

    # 2. Read the existing project information.
    title = (project.title or "Untitled project").strip()
    description = (project.description or "").strip()
    category = str(project.category or "General").strip()

    skills = _to_string_list(project.required_skills)
    expected_deliverables = _to_string_list(
        project.expected_deliverables
    )

    start_date = _to_datetime(project.start_date)
    due_date = _to_datetime(project.due_date)

    # 3. Determine the estimated project duration.
    if start_date and due_date:
        duration_days = max(
            1,
            (due_date.date() - start_date.date()).days,
        )
    else:
        duration_days = 30

    duration_days = min(duration_days, 3650)

    # If only a deadline is provided, calculate a suggested start
    # date for scheduling the milestone recommendations.
    schedule_start = start_date

    if schedule_start is None and due_date is not None:
        schedule_start = due_date - timedelta(days=duration_days)

    # 4. Prepare project objectives.
    objectives = [
        f"Complete the project: {title}.",
        f"Deliver work aligned with the project category: {category}.",
    ]

    if description:
        objectives.append(
            f"Address the requirements described in the project brief: "
            f"{description}"
        )

    if expected_deliverables:
        objectives.append(
            "Complete the deliverables agreed for this project."
        )

    if skills:
        objectives.append(
            "Use the relevant skills identified in the project requirements: "
            + ", ".join(skills)
            + "."
        )

    # 5. Prepare deliverables.
    deliverables = expected_deliverables or [
        "Completion of the requirements agreed in the project description."
    ]

    # 6. Prepare the work breakdown.
    scope_of_work = [
        "Review the project title, description, requirements and expected deliverables.",
        "Confirm the project scope and organize the agreed work into milestones.",
        "Carry out the implementation required by the agreed project deliverables.",
        "Review the completed work against the agreed requirements and acceptance criteria.",
        "Prepare the agreed deliverables for client review and final handover.",
    ]

    if skills:
        scope_of_work.append(
            "Apply the following project skills where relevant: "
            + ", ".join(skills)
            + "."
        )

    if additional_instructions and additional_instructions.strip():
        scope_of_work.append(
            "Consider the following additional client instructions during "
            "scope review: "
            + additional_instructions.strip()
        )

    # 7. Generate three milestones.
    milestone_definitions = [
        {
            "title": "Requirements and Planning",
            "description": (
                "Review the project brief, clarify the agreed requirements, "
                "and organize the work into a practical implementation plan."
            ),
            "deliverables": [
                "Reviewed project requirements and confirmed deliverable checklist."
            ],
            "percentage": Decimal("30.00"),
            "fraction": 0.30,
            "criteria": [
                "Project requirements have been reviewed.",
                "Expected deliverables have been identified.",
                "The milestone plan is ready for client review.",
            ],
            "review_days": 3,
        },
        {
            "title": "Project Implementation",
            "description": (
                "Carry out the main project work according to the approved "
                "requirements and agreed deliverables."
            ),
            "deliverables": deliverables,
            "percentage": Decimal("40.00"),
            "fraction": 0.70,
            "criteria": [
                "The agreed implementation work has been completed.",
                "Expected deliverables are available for review.",
                "The work follows the agreed project requirements.",
            ],
            "review_days": 5,
        },
        {
            "title": "Testing and Final Handover",
            "description": (
                "Review the completed work, address agreed corrections, "
                "and prepare the final deliverables for client handover."
            ),
            "deliverables": [
                "Completed project deliverables.",
                "Final handover of the agreed work.",
            ],
            "percentage": Decimal("30.00"),
            "fraction": 1.0,
            "criteria": [
                "Completed work has been checked against acceptance criteria.",
                "Agreed corrections have been addressed.",
                "Final deliverables have been submitted to the client.",
            ],
            "review_days": 5,
        },
    ]

    milestones = []

    for definition in milestone_definitions:
        milestone = MilestoneRecommendation(
            title=definition["title"],
            description=definition["description"],
            deliverables=definition["deliverables"],
            allocation_percentage=definition["percentage"],
            amount=Decimal("1.00"),
            suggested_submission_date=_make_milestone_date(
                schedule_start,
                duration_days,
                definition["fraction"],
            ),
            review_period_days=definition["review_days"],
            completion_criteria=definition["criteria"],
        )

        milestones.append(milestone)

    # 8. Build the complete scope using the existing Pydantic schema.
    scope_data = ProjectScopeData(
        project_objectives=objectives,
        detailed_scope_of_work=scope_of_work,
        deliverables=deliverables,
        milestones=milestones,
        estimated_duration_days=duration_days,
        suggested_budget_allocation=[],
        acceptance_criteria=[
            "All explicitly agreed project deliverables are submitted.",
            "Completed work is consistent with the project description.",
            "The client can review the work against the agreed completion criteria.",
            "Final deliverables are handed over to the client.",
        ],
        revision_limits=(
            "Revisions should address deviations from the agreed scope. "
            "Requests for additional features or work outside the agreed "
            "deliverables should be discussed separately."
        ),
        client_responsibilities=[
            "Provide accurate project requirements and relevant information.",
            "Review submitted milestones and provide feedback.",
            "Clarify questions that arise during project execution.",
            "Approve completed work according to the agreed criteria.",
        ],
        freelancer_responsibilities=[
            "Complete the agreed project work.",
            "Communicate progress and raise blockers promptly.",
            "Submit milestone deliverables for client review.",
            "Address agreed corrections within the project scope.",
        ],
        dependencies_and_assumptions=[
            "The project information supplied by the client is accurate.",
            "The client will provide necessary information and feedback.",
            "The project timeline depends on timely communication and reviews.",
            "The generated scope is a draft and should be reviewed by both parties.",
        ],
        out_of_scope_activities=[
            "Features or services not included in the project description "
            "or agreed deliverables.",
            "Additional work introduced after scope approval unless "
            "both parties agree to a scope change.",
        ],
    )

    # 9. Reconcile milestone percentages and amounts.
    validated = reconcile_scope_data(
        scope_data,
        budget,
    )

    # 10. Find the next scope version.
    latest_version = (
        db.query(AIScopeVersion)
        .filter(
            AIScopeVersion.project_id == project.id
        )
        .order_by(
            AIScopeVersion.version_number.desc()
        )
        .first()
    )

    version_number = (
        latest_version.version_number + 1
        if latest_version
        else 1
    )

    # 11. Save the scope as an unapproved draft.
    scope = AIScopeVersion(
        project_id=project.id,
        version_number=version_number,
        scope_data=validated.model_dump(mode="json"),
        status="draft",
        is_approved=False,
        generated_by=user_id,
    )

    try:
        db.add(scope)
        db.commit()
        db.refresh(scope)

    except Exception:
        db.rollback()
        raise

    return scope
