import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models import (
    User,
    Milestone,
    Project,
    MilestoneAudit,
)
from app.schemas.milestone import (
    MilestoneProgressUpdate,
    MilestoneSubmissionRequest,
    MilestoneReviewRequest,
    MilestoneDisputeRequest,
    MilestoneResponse,
)
from app.services.file_validation import validate_file_content
from app.services.milestone_service import (
    get_milestone,
    verify_project_participant,
    update_milestone_progress,
    submit_milestone,
    start_milestone_review,
    review_milestone,
    raise_milestone_dispute,
)

router = APIRouter(prefix="/milestones", tags=["Milestones"])

STORAGE_DIR = (Path(__file__).resolve().parents[3] / "storage" / "deliverables").resolve()
MAX_FILE_SIZE = 10 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    ".pdf", ".png", ".jpg", ".jpeg",
    ".docx", ".xlsx", ".zip", ".txt",
}


@router.get("/projects/{project_id}",
            response_model=list[MilestoneResponse])
def list_project_milestones(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(
        Project.id == project_id
    ).first()

    if not project:
        raise HTTPException(404, "Project not found.")

    if current_user.id not in [
        project.client_id,
        project.freelancer_id,
    ]:
        raise HTTPException(403, "Not a project participant.")

    return (
    db.query(Milestone)
    .filter(
        Milestone.project_id == project_id,
        Milestone.is_current.is_(True),
    )
    .order_by(Milestone.id.asc())
    .all()
)


@router.get("/{milestone_id}",
            response_model=MilestoneResponse)
def get_milestone_details(
    milestone_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    milestone = get_milestone(db, milestone_id)
    verify_project_participant(milestone, current_user)
    return milestone


@router.patch("/{milestone_id}/progress",
              response_model=MilestoneResponse)
def update_progress(
    milestone_id: int,
    request: MilestoneProgressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_milestone_progress(
        db,
        milestone_id,
        current_user,
        request.progress_percentage,
    )


@router.post("/{milestone_id}/upload")
async def upload_deliverable(
    milestone_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    milestone = get_milestone(db, milestone_id)

    from app.services.milestone_service import verify_freelancer
    verify_freelancer(milestone, current_user)

    if milestone.status not in ["in_progress", "revision_requested"]:
        raise HTTPException(
            409,
            "Files can only be uploaded while work is in progress or revisions are requested.",
        )

    extension = Path(file.filename or "").suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(415, "Unsupported file type.")

    content = await file.read(MAX_FILE_SIZE + 1)

    if not content or len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, "File is empty or exceeds 10 MB.")
    if not validate_file_content(file.filename or "", content):
        raise HTTPException(415, "File content does not match its extension or is not valid UTF-8 text.")

    STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    stored_name = f"{uuid.uuid4().hex}{extension}"
    destination = STORAGE_DIR / stored_name

    try:
        with destination.open("xb") as output:
            output.write(content)
    except OSError:
        raise HTTPException(500, "Unable to store the uploaded file.")

    # Store only the generated identifier, never a public filesystem path.
    existing = milestone.submission_url

    if existing:
        existing_files = [
            item for item in existing.split(",") if item
        ]
    else:
        existing_files = []

    existing_files.append(stored_name)
    milestone.submission_url = ",".join(existing_files)

    try:
        db.commit()
    except Exception:
        db.rollback()
        destination.unlink(missing_ok=True)
        raise

    return {
        "message": "Deliverable uploaded successfully.",
        "file_id": stored_name,
    }


@router.get("/files/{file_id}")
def download_deliverable(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if Path(file_id).name != file_id:
        raise HTTPException(400, "Invalid file identifier.")

    milestone = (
        db.query(Milestone)
        .filter(Milestone.submission_url.contains(file_id))
        .first()
    )

    if not milestone or file_id not in (milestone.submission_url or "").split(","):
        raise HTTPException(404, "Deliverable not found.")

    verify_project_participant(milestone, current_user)

    file_path = (STORAGE_DIR / file_id).resolve()

    if file_path.parent != STORAGE_DIR or not file_path.is_file():
        raise HTTPException(404, "Deliverable file not found.")

    return FileResponse(
        path=file_path,
        filename=file_id,
        media_type="application/octet-stream",
    )


@router.post("/{milestone_id}/submit",
             response_model=MilestoneResponse)
def submit_work(
    milestone_id: int,
    request: MilestoneSubmissionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    milestone = get_milestone(db, milestone_id)
    uploaded_ids = set((milestone.submission_url or "").split(","))
    submitted_ids = {item.strip() for item in request.submission_url.split(",") if item.strip()}
    if not submitted_ids:
        raise HTTPException(422, "Upload at least one deliverable before submitting.")
    if not submitted_ids.issubset(uploaded_ids):
        raise HTTPException(403, "Submission contains files that were not uploaded to this milestone.")
    return submit_milestone(
        db, milestone_id, current_user, ",".join(sorted(submitted_ids)),
        request.submission_notes,
    )


@router.post("/{milestone_id}/start-review",
             response_model=MilestoneResponse)
def start_review(
    milestone_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return start_milestone_review(
        db,
        milestone_id,
        current_user,
    )


@router.post("/{milestone_id}/review",
             response_model=MilestoneResponse)
def review_work(
    milestone_id: int,
    request: MilestoneReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return review_milestone(
        db,
        milestone_id,
        current_user,
        request.action,
        request.explanation,
    )


@router.post("/{milestone_id}/dispute",
             response_model=MilestoneResponse)
def dispute_milestone(
    milestone_id: int,
    request: MilestoneDisputeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return raise_milestone_dispute(
        db,
        milestone_id,
        current_user,
        request.explanation,
    )


@router.get("/{milestone_id}/audit")
def get_milestone_audit(
    milestone_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    milestone = get_milestone(db, milestone_id)
    verify_project_participant(milestone, current_user)

    return (
        db.query(MilestoneAudit)
        .filter(MilestoneAudit.milestone_id == milestone_id)
        .order_by(MilestoneAudit.created_at.desc())
        .all()
    )