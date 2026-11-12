from app.api.routes.auth import (
    require_role,
    get_current_user,
)
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import (
    User,
    UserRole,
    Project,
    Application,
    ApplicationStatusHistory,
    Notification,
)
from app.api.routes.auth import require_role

from app.schemas.project import (
    ProjectCreate,
    ProjectResponse,
    ApplicationCreate,
    ApplicationResponse,
    ApplicationStatusUpdate,
)


router = APIRouter(prefix="/projects", tags=["Projects"])


def _application_response(application):
    project = application.project
    freelancer = application.freelancer
    profile = freelancer.freelancer_profile if freelancer else None
    return {
        "id": application.id,
        "project_id": application.project_id,
        "freelancer_id": application.freelancer_id,
        "proposal_text": application.proposal_text,
        "proposed_amount": application.proposed_amount,
        "estimated_completion_days": application.estimated_completion_days,
        "relevant_experience": application.relevant_experience,
        "status": application.status,
        "created_at": application.created_at,
        "updated_at": application.updated_at,
        "project_title": project.title if project else None,
        "currency": project.currency if project else None,
        "freelancer_name": freelancer.full_name if freelancer else None,
        "freelancer_email": freelancer.email if freelancer else None,
        "freelancer_country": freelancer.country if freelancer else None,
        "freelancer_title": profile.professional_title if profile else None,
        "freelancer_skills": profile.skills if profile else None,
        "freelancer_experience_years": profile.experience_years if profile else None,
    }


# --------------------------------------------------
# CLIENT: CREATE PROJECT
# --------------------------------------------------

@router.post("/", response_model=ProjectResponse, status_code=201)
def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CLIENT)),
):
    project = Project(
        client_id=current_user.id,
        title=data.title,
        description=data.description,
        required_skills=data.required_skills,
        category=data.category,
        budget=data.budget,
        currency=data.currency,
        status="open",
        start_date=data.start_date,
        due_date=data.due_date,
        expected_deliverables=data.expected_deliverables,
        experience_level=data.experience_level,
        project_type=data.project_type,
        preferred_milestone_structure=data.preferred_milestone_structure,
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return project


# --------------------------------------------------
# CLIENT: VIEW OWN PROJECTS
# --------------------------------------------------

@router.get("/mine", response_model=list[ProjectResponse])
def get_my_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CLIENT)),
):
    return (
        db.query(Project)
        .filter(Project.client_id == current_user.id)
        .order_by(Project.created_at.desc())
        .all()
    )


# --------------------------------------------------
# FREELANCER: DISCOVER PROJECTS
# --------------------------------------------------

@router.get("/", response_model=list[ProjectResponse])
def discover_projects(
    search: str | None = None,
    category: str | None = None,
    min_budget: Decimal | None = Query(default=None, gt=0),
    max_budget: Decimal | None = Query(default=None, gt=0),
    experience_level: str | None = None,
    project_type: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.FREELANCER)),
):
    query = db.query(Project).filter(Project.status == "open")

    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            Project.title.ilike(term)
            | Project.description.ilike(term)
        )

    if category:
        query = query.filter(Project.category.ilike(category.strip()))

    if min_budget is not None:
        query = query.filter(Project.budget >= min_budget)

    if max_budget is not None:
        query = query.filter(Project.budget <= max_budget)

    if experience_level:
        query = query.filter(Project.experience_level == experience_level)

    if project_type:
        query = query.filter(Project.project_type == project_type)

    return (
        query.order_by(Project.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# --------------------------------------------------
# VIEW PROJECT DETAILS
# --------------------------------------------------

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project_details(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    if current_user.role == UserRole.CLIENT:
        if project.client_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied.")

    elif current_user.role == UserRole.FREELANCER:
        if project.status != "open" and project.freelancer_id != current_user.id:
            raise HTTPException(status_code=403, detail="Project is not available.")

    else:
        raise HTTPException(status_code=403, detail="Access denied.")

    return project


# --------------------------------------------------
# FREELANCER: APPLY TO PROJECT
# --------------------------------------------------

@router.post(
    "/{project_id}/applications",
    response_model=ApplicationResponse,
    status_code=201,
)
def apply_to_project(
    project_id: int,
    data: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.FREELANCER)),
):
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project or project.status != "open":
        raise HTTPException(
            status_code=404,
            detail="Project is not available for applications.",
        )

    if project.client_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="You cannot apply to your own project.",
        )

    existing = (
        db.query(Application)
        .filter(
            Application.project_id == project_id,
            Application.freelancer_id == current_user.id,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="You have already applied to this project.",
        )

    application = Application(
        project_id=project_id,
        freelancer_id=current_user.id,
        proposal_text=data.proposal_text,
        proposed_amount=data.proposed_amount,
        estimated_completion_days=data.estimated_completion_days,
        relevant_experience=data.relevant_experience,
        status="pending",
    )

    db.add(application)
    db.flush()
    db.add(Notification(user_id=project.client_id, title="New freelancer application", message=f"{current_user.full_name} applied to '{project.title}'."))

    db.add(
        ApplicationStatusHistory(
            application_id=application.id,
            previous_status=None,
            new_status="pending",
            changed_by=current_user.id,
        )
    )

    db.commit()
    db.refresh(application)

    return application


# --------------------------------------------------
# FREELANCER: VIEW OWN APPLICATIONS
# --------------------------------------------------

@router.get("/applications/mine", response_model=list[ApplicationResponse])
def get_my_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.FREELANCER)),
):
    rows = (
        db.query(Application)
        .filter(Application.freelancer_id == current_user.id)
        .order_by(Application.created_at.desc())
        .all()
    )
    return [_application_response(row) for row in rows]


# --------------------------------------------------
# FREELANCER: WITHDRAW APPLICATION
# --------------------------------------------------

@router.post("/applications/{application_id}/withdraw")
def withdraw_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.FREELANCER)),
):
    application = (
        db.query(Application)
        .filter(
            Application.id == application_id,
            Application.freelancer_id == current_user.id,
        )
        .first()
    )

    if not application:
        raise HTTPException(status_code=404, detail="Application not found.")

    if application.status not in ("pending", "shortlisted"):
        raise HTTPException(
            status_code=400,
            detail="This application cannot be withdrawn.",
        )

    previous_status = application.status
    application.status = "withdrawn"

    db.add(
        ApplicationStatusHistory(
            application_id=application.id,
            previous_status=previous_status,
            new_status="withdrawn",
            changed_by=current_user.id,
        )
    )

    db.commit()

    return {"message": "Application withdrawn successfully."}


# --------------------------------------------------
# CLIENT: VIEW APPLICATIONS FOR OWN PROJECT
# --------------------------------------------------

@router.get(
    "/{project_id}/applications",
    response_model=list[ApplicationResponse],
)
def get_project_applications(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CLIENT)),
):
    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.client_id == current_user.id,
        )
        .first()
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    rows = (
        db.query(Application)
        .filter(Application.project_id == project_id)
        .order_by(Application.created_at.desc())
        .all()
    )
    return [_application_response(row) for row in rows]


# --------------------------------------------------
# CLIENT: SHORTLIST OR REJECT APPLICATION
# --------------------------------------------------

@router.patch("/applications/{application_id}/status")
def update_application_status(
    application_id: int,
    data: ApplicationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CLIENT)),
):
    application = (
        db.query(Application)
        .join(Project)
        .filter(
            Application.id == application_id,
            Project.client_id == current_user.id,
        )
        .first()
    )

    if not application:
        raise HTTPException(status_code=404, detail="Application not found.")

    if application.status not in ("pending", "shortlisted"):
        raise HTTPException(
            status_code=400,
            detail="Application status cannot be changed.",
        )

    if application.project.status != "open":
        raise HTTPException(
            status_code=400,
            detail="This project is no longer accepting applications.",
        )

    previous_status = application.status
    application.status = data.status

    db.add(
        ApplicationStatusHistory(
            application_id=application.id,
            previous_status=previous_status,
            new_status=data.status,
            changed_by=current_user.id,
        )
    )

    db.commit()

    return {"message": f"Application {data.status} successfully."}


# --------------------------------------------------
# CLIENT: HIRE FREELANCER
# --------------------------------------------------

@router.post("/applications/{application_id}/hire")
def hire_freelancer(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CLIENT)),
):
    application = (
        db.query(Application)
        .filter(Application.id == application_id)
        .first()
    )

    if not application:
        raise HTTPException(status_code=404, detail="Application not found.")

    project = (
        db.query(Project)
        .filter(
            Project.id == application.project_id,
            Project.client_id == current_user.id,
        )
        .with_for_update()
        .first()
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    if project.status != "open" or project.freelancer_id is not None:
        raise HTTPException(
            status_code=409,
            detail="This project has already been assigned or closed.",
        )

    if application.status not in ("pending", "shortlisted"):
        raise HTTPException(
            status_code=400,
            detail="Only pending or shortlisted applications can be accepted.",
        )

    try:
        previous_status = application.status

        project.freelancer_id = application.freelancer_id
        project.status = "in_progress"

        application.status = "accepted"

        db.add(
            ApplicationStatusHistory(
                application_id=application.id,
                previous_status=previous_status,
                new_status="accepted",
                changed_by=current_user.id,
            )
        )

        competing_applications = (
            db.query(Application)
            .filter(
                Application.project_id == project.id,
                Application.id != application.id,
                Application.status.in_(["pending", "shortlisted"]),
            )
            .with_for_update()
            .all()
        )

        db.add(Notification(user_id=application.freelancer_id, title="You were hired", message=f"You were selected for '{project.title}'. Open the project workspace to agree the scope and milestones."))
        for competing in competing_applications:
            old_status = competing.status
            competing.status = "rejected"
            db.add(Notification(user_id=competing.freelancer_id, title="Application update", message=f"The client selected another freelancer for '{project.title}'."))

            db.add(
                ApplicationStatusHistory(
                    application_id=competing.id,
                    previous_status=old_status,
                    new_status="rejected",
                    changed_by=current_user.id,
                )
            )

        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "message": "Freelancer hired successfully.",
        "project_id": project.id,
        "freelancer_id": project.freelancer_id,
        "application_id": application.id,
        "project_status": project.status,
    }