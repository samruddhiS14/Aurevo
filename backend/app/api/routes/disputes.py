from pathlib import Path
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models import User, Project, Milestone, Dispute, DisputeEvidence, MilestoneAudit, Notification, Agreement, AgreementVersion
from app.services.gemini_service import GeminiService
from app.services.gemini_errors import GeminiUnavailableError, GeminiInvalidResponseError
from app.services.file_validation import validate_file_content
from app.core.config import settings
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/v1/disputes", tags=["Disputes"])
EVIDENCE_DIR = (Path(__file__).resolve().parents[3] / "storage" / "disputes").resolve()
MAX_EVIDENCE_SIZE = 10 * 1024 * 1024
ALLOWED = {".pdf", ".png", ".jpg", ".jpeg", ".docx", ".xlsx", ".zip", ".txt", ".csv"}

class DisputeCreate(BaseModel):
    reason: str = Field(min_length=20, max_length=10000)

class EvidenceCreate(BaseModel):
    description: str = Field(min_length=5, max_length=5000)

class DisputeResolutionProposal(BaseModel):
    summary: str = Field(min_length=20, max_length=5000)
    milestone_outcome: Literal["submitted", "revision_requested"]


def _participants(db, milestone, user):
    project = db.get(Project, milestone.project_id)
    if not project or user.id not in (project.client_id, project.freelancer_id):
        raise HTTPException(403, "Only project participants can access this dispute.")
    return project


def _dispute_for_user(db, dispute_id, user):
    dispute = db.get(Dispute, dispute_id)
    if not dispute:
        raise HTTPException(404, "Dispute not found.")
    milestone = db.get(Milestone, dispute.milestone_id)
    project = _participants(db, milestone, user)
    return dispute, milestone, project

@router.post("/milestones/{milestone_id}")
def create_dispute(milestone_id: int, payload: DisputeCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    milestone = db.query(Milestone).filter(Milestone.id == milestone_id).with_for_update().first()
    if not milestone:
        raise HTTPException(404, "Milestone not found.")
    project = _participants(db, milestone, user)
    if milestone.status in ("paid", "disputed"):
        raise HTTPException(409, "A dispute cannot be opened for this milestone status.")
    existing = db.query(Dispute).filter(Dispute.milestone_id == milestone_id, Dispute.status.in_(("open", "under_review"))).first()
    if existing:
        raise HTTPException(409, "An active dispute already exists for this milestone.")
    dispute = Dispute(project_id=project.id, milestone_id=milestone.id, raised_by=user.id, reason=payload.reason.strip(), status="open")
    old = milestone.status
    milestone.status = "disputed"
    db.add(dispute); db.flush()
    db.add(MilestoneAudit(milestone_id=milestone.id, actor_user_id=user.id, previous_status=old, new_status="disputed", description="A participant opened an evidence-based dispute.", details={"dispute_id": dispute.id}))
    other_id = project.freelancer_id if user.id == project.client_id else project.client_id
    db.add(Notification(user_id=other_id, title="A milestone dispute was opened", message=f"A dispute was opened for '{milestone.title}'. Add your evidence in the project workspace."))
    db.commit(); db.refresh(dispute)
    return {"id": dispute.id, "project_id": dispute.project_id, "milestone_id": dispute.milestone_id, "reason": dispute.reason, "status": dispute.status, "created_at": dispute.created_at}

@router.post("/{dispute_id}/evidence")
def add_evidence(dispute_id: int, payload: EvidenceCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    dispute, _, _ = _dispute_for_user(db, dispute_id, user)
    if dispute.status not in ("open", "under_review"):
        raise HTTPException(409, "Evidence cannot be added to a closed dispute.")
    evidence = DisputeEvidence(dispute_id=dispute.id, submitted_by=user.id, description=payload.description.strip())
    db.add(evidence); db.commit(); db.refresh(evidence)
    return {"id": evidence.id, "description": evidence.description, "submitted_by": evidence.submitted_by, "created_at": evidence.created_at}

@router.post("/{dispute_id}/evidence/file")
async def upload_evidence(dispute_id: int, description: str = Form(..., min_length=5, max_length=5000), file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    dispute, _, _ = _dispute_for_user(db, dispute_id, user)
    if dispute.status not in ("open", "under_review"):
        raise HTTPException(409, "Evidence cannot be added to a closed dispute.")
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED:
        raise HTTPException(415, "Unsupported evidence file type.")
    content = await file.read(MAX_EVIDENCE_SIZE + 1)
    if not content or len(content) > MAX_EVIDENCE_SIZE:
        raise HTTPException(413, "Evidence file must be between 1 byte and 10 MB.")
    if not validate_file_content(file.filename or "", content):
        raise HTTPException(415, "Evidence content does not match its file extension or is not valid UTF-8 text.")
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}{ext}"
    path = EVIDENCE_DIR / name
    path.write_bytes(content)
    item = DisputeEvidence(dispute_id=dispute.id, submitted_by=user.id, description=description[:5000], file_name=Path(file.filename or name).name, file_path=str(path), mime_type=file.content_type)
    db.add(item)
    try:
        db.commit()
        db.refresh(item)
    except Exception:
        db.rollback()
        path.unlink(missing_ok=True)
        raise
    return {"id": item.id, "description": item.description, "file_name": item.file_name, "created_at": item.created_at}

@router.get("/{dispute_id}")
def get_dispute(dispute_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    dispute, milestone, project = _dispute_for_user(db, dispute_id, user)
    evidence = db.query(DisputeEvidence).filter(DisputeEvidence.dispute_id == dispute.id).order_by(DisputeEvidence.created_at.asc()).all()
    timeline = db.query(MilestoneAudit).filter(MilestoneAudit.milestone_id == milestone.id).order_by(MilestoneAudit.created_at.asc()).all()
    return {"id": dispute.id, "project_id": project.id, "milestone_id": milestone.id, "milestone_title": milestone.title, "reason": dispute.reason, "status": dispute.status, "ai_report": dispute.ai_report, "resolution_summary": dispute.resolution_summary, "resolution_outcome": dispute.resolution_outcome, "resolution_proposed_by": dispute.resolution_proposed_by, "client_accepted": dispute.client_accepted, "freelancer_accepted": dispute.freelancer_accepted, "created_at": dispute.created_at,
        "evidence": [{"id": e.id, "submitted_by": e.submitted_by, "description": e.description, "file_name": e.file_name, "created_at": e.created_at} for e in evidence],
        "timeline": [{"previous_status": t.previous_status, "new_status": t.new_status, "description": t.description, "created_at": t.created_at} for t in timeline]}

@router.post("/{dispute_id}/ai-report")
def generate_ai_report(dispute_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    dispute, milestone, project = _dispute_for_user(db, dispute_id, user)
    evidence = db.query(DisputeEvidence).filter(DisputeEvidence.dispute_id == dispute.id).order_by(DisputeEvidence.created_at.asc()).all()
    agreement = db.query(Agreement).filter(Agreement.project_id == project.id).first()
    version = db.get(AgreementVersion, agreement.active_version_id) if agreement and agreement.active_version_id else None
    context = {
        "project": {"title": project.title, "description": project.description},
        "milestone": {"title": milestone.title, "description": milestone.description, "deliverables": milestone.deliverables, "completion_criteria": milestone.completion_criteria, "submission_notes": milestone.submission_notes, "submission_url": milestone.submission_url, "status": milestone.status},
        "agreement": version.agreement_data if version else None,
        "dispute_reason": dispute.reason,
        "evidence": [{"submitted_by": e.submitted_by, "description": e.description, "file_name": e.file_name} for e in evidence],
    }
    prompt = "You are a neutral dispute evidence analyst. Produce JSON with keys: factual_timeline, agreed_scope_references, evidence_from_client, evidence_from_freelancer, unresolved_questions, balanced_considerations, suggested_process_steps, limitations. Be neutral, identify missing evidence, do not assume facts, do not decide fault, do not recommend who should win, and do not make payment decisions. Explicitly state this is advisory and human review is required. Context: " + __import__("json").dumps(context, default=str)
    try:
        report = GeminiService().generate_json(prompt)
    except GeminiUnavailableError:
        raise HTTPException(503, "AI dispute analysis is temporarily unavailable. The dispute and evidence remain saved.", headers={"Retry-After": "30"})
    except GeminiInvalidResponseError:
        raise HTTPException(502, "AI returned an invalid dispute analysis. Please retry; the dispute and evidence remain saved.")
    report["advisory_only"] = True
    report["decision_made"] = False
    report["disclaimer"] = "AI-generated evidence summary only. It is not a ruling, legal advice, or a payment instruction. Both parties retain the right to respond and a human must review the evidence."
    dispute.ai_report = report
    db.commit()
    return report

@router.get("/projects/{project_id}")
def list_project_disputes(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    project = db.get(Project, project_id)
    if not project or user.id not in (project.client_id, project.freelancer_id):
        raise HTTPException(404, "Project not found.")
    rows = db.query(Dispute).filter(Dispute.project_id == project_id).order_by(Dispute.created_at.desc()).all()
    return [{"id": d.id, "milestone_id": d.milestone_id, "reason": d.reason, "status": d.status, "created_at": d.created_at} for d in rows]

@router.get("/{dispute_id}/evidence/{evidence_id}/file")
def download_evidence(dispute_id: int, evidence_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    dispute, _, _ = _dispute_for_user(db, dispute_id, user)
    evidence = db.query(DisputeEvidence).filter(DisputeEvidence.id == evidence_id, DisputeEvidence.dispute_id == dispute.id).first()
    if not evidence or not evidence.file_path:
        raise HTTPException(404, "Evidence file not found.")
    path = Path(evidence.file_path).resolve()
    if path.parent != EVIDENCE_DIR or not path.is_file():
        raise HTTPException(404, "Evidence file is unavailable.")
    return FileResponse(path, filename=evidence.file_name or path.name, media_type=evidence.mime_type or "application/octet-stream")

@router.post("/{dispute_id}/propose-resolution")
def propose_resolution(dispute_id: int, payload: DisputeResolutionProposal, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    dispute, milestone, project = _dispute_for_user(db, dispute_id, user)
    if dispute.status not in ("open", "under_review"):
        raise HTTPException(409, "This dispute is not open for a resolution proposal.")
    dispute.resolution_summary = payload.summary.strip()
    dispute.resolution_outcome = payload.milestone_outcome
    dispute.resolution_proposed_by = user.id
    dispute.client_accepted = user.id == project.client_id
    dispute.freelancer_accepted = user.id == project.freelancer_id
    dispute.status = "under_review"
    other_id = project.freelancer_id if user.id == project.client_id else project.client_id
    db.add(Notification(user_id=other_id, title="Dispute resolution proposal", message=f"A resolution proposal is ready for '{milestone.title}'. Review and accept or reject it."))
    db.commit()
    return {"id": dispute.id, "status": dispute.status, "summary": dispute.resolution_summary, "milestone_outcome": dispute.resolution_outcome, "awaiting_acceptance_from": "freelancer" if user.id == project.client_id else "client"}

@router.post("/{dispute_id}/accept-resolution")
def accept_resolution(dispute_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    dispute, milestone, project = _dispute_for_user(db, dispute_id, user)
    if dispute.status != "under_review" or not dispute.resolution_summary or not dispute.resolution_outcome:
        raise HTTPException(409, "There is no pending resolution proposal.")
    if dispute.resolution_proposed_by == user.id:
        raise HTTPException(409, "The proposer cannot accept their own proposal.")
    if user.id == project.client_id:
        dispute.client_accepted = True
    else:
        dispute.freelancer_accepted = True
    if dispute.client_accepted and dispute.freelancer_accepted:
        now = datetime.now(timezone.utc)
        previous = milestone.status
        milestone.status = dispute.resolution_outcome
        if dispute.resolution_outcome == "submitted":
            milestone.submitted_at = now
            review_window = timedelta(minutes=settings.MILESTONE_REVIEW_MINUTES) if settings.MILESTONE_REVIEW_MINUTES > 0 else timedelta(hours=settings.MILESTONE_REVIEW_HOURS)
            milestone.review_deadline = now + review_window
        else:
            milestone.revision_explanation = dispute.resolution_summary
        dispute.status = "resolved"
        db.add(MilestoneAudit(milestone_id=milestone.id, actor_user_id=user.id, previous_status=previous, new_status=milestone.status, description="Both project participants accepted a dispute resolution proposal.", details={"dispute_id": dispute.id, "resolution_summary": dispute.resolution_summary, "outcome": dispute.resolution_outcome}))
        db.add(Notification(user_id=project.client_id, title="Dispute resolved by mutual agreement", message=f"The dispute for '{milestone.title}' is resolved. Milestone status: {milestone.status}."))
        db.add(Notification(user_id=project.freelancer_id, title="Dispute resolved by mutual agreement", message=f"The dispute for '{milestone.title}' is resolved. Milestone status: {milestone.status}."))
    else:
        other_id = project.freelancer_id if user.id == project.client_id else project.client_id
        db.add(Notification(user_id=other_id, title="Resolution accepted", message="One participant accepted the resolution proposal. Your acceptance is still required."))
    db.commit()
    return {"id": dispute.id, "status": dispute.status, "client_accepted": dispute.client_accepted, "freelancer_accepted": dispute.freelancer_accepted, "milestone_status": milestone.status}

@router.post("/{dispute_id}/reject-resolution")
def reject_resolution(dispute_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    dispute, milestone, project = _dispute_for_user(db, dispute_id, user)
    if dispute.status != "under_review" or not dispute.resolution_summary:
        raise HTTPException(409, "There is no pending resolution proposal.")
    if dispute.resolution_proposed_by == user.id:
        raise HTTPException(409, "The proposer cannot reject their own proposal.")
    dispute.resolution_summary = None
    dispute.resolution_outcome = None
    dispute.resolution_proposed_by = None
    dispute.client_accepted = False
    dispute.freelancer_accepted = False
    dispute.status = "open"
    other_id = project.freelancer_id if user.id == project.client_id else project.client_id
    db.add(Notification(user_id=other_id, title="Resolution proposal declined", message=f"The proposal for '{milestone.title}' was declined. The dispute remains open."))
    db.commit()
    return {"id": dispute.id, "status": dispute.status}
