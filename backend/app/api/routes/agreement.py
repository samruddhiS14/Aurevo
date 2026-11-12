from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models import (
    User,
    Project,
    Agreement,
    AgreementVersion,
    AgreementAudit,
)
from app.schemas.agreement import (
    AgreementGenerateRequest,
    AgreementVersionCreate,
    AgreementApprovalRequest,
    AgreementVersionResponse,
    AgreementAuditResponse,
)
from app.services.agreement_service import (
    generate_initial_agreement,
    create_agreement_version,
    approve_agreement_version,
)

router = APIRouter(prefix="/agreements", tags=["Agreements"])


def verify_participant(db, project_id, user):
    project = db.query(Project).filter(
        Project.id == project_id
    ).first()

    if not project:
        raise HTTPException(404, "Project not found.")

    if user.id not in [project.client_id, project.freelancer_id]:
        raise HTTPException(403, "Not a project participant.")

    return project


@router.post("/projects/{project_id}/generate",
             response_model=AgreementVersionResponse)
def generate_agreement(
    project_id: int,
    request: AgreementGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return generate_initial_agreement(
        db,
        project_id,
        current_user,
    )


@router.get("/projects/{project_id}/versions")
def get_agreement_versions(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_participant(db, project_id, current_user)

    agreement = db.query(Agreement).filter(
        Agreement.project_id == project_id
    ).first()

    if not agreement:
        return []

    return (
        db.query(AgreementVersion)
        .filter(AgreementVersion.agreement_id == agreement.id)
        .order_by(AgreementVersion.version_number.desc())
        .all()
    )


@router.get("/projects/{project_id}/active")
def get_active_agreement(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_participant(db, project_id, current_user)

    agreement = db.query(Agreement).filter(
        Agreement.project_id == project_id
    ).first()

    if not agreement or not agreement.active_version_id:
        raise HTTPException(404, "No active agreement exists.")

    return db.query(AgreementVersion).filter(
        AgreementVersion.id == agreement.active_version_id
    ).first()


@router.post("/{agreement_id}/versions",
             response_model=AgreementVersionResponse)
def create_version(
    agreement_id: int,
    request: AgreementVersionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_agreement_version(
        db=db,
        agreement_id=agreement_id,
        current_user=current_user,
        agreement_data=request.agreement_data.model_dump(mode="json"),
        change_summary=request.change_summary,
    )


@router.post("/versions/{version_id}/approve",
             response_model=AgreementVersionResponse)
def approve_version(
    version_id: int,
    request: AgreementApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    version = approve_agreement_version(
        db,
        version_id,
        current_user,
    )

    if version.status == "active":
        from app.services.milestone_service import (
            create_milestones_from_agreement,
        )

        create_milestones_from_agreement(
            db,
            version,
            current_user.id,
        )

    return version


@router.get("/projects/{project_id}/audit",
            response_model=list[AgreementAuditResponse])
def get_agreement_audit(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_participant(db, project_id, current_user)

    agreement = db.query(Agreement).filter(
        Agreement.project_id == project_id
    ).first()

    if not agreement:
        raise HTTPException(404, "Agreement not found.")

    return (
        db.query(AgreementAudit)
        .filter(AgreementAudit.agreement_id == agreement.id)
        .order_by(AgreementAudit.created_at.desc())
        .all()
    )