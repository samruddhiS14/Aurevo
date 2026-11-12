import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models import User, Project, ProjectMessage, Notification
from app.services.file_validation import validate_file_content
from app.services.policy_detector import off_platform_reasons

router = APIRouter(tags=["Project Workspace"])
CHAT_STORAGE = (Path(__file__).resolve().parents[3] / "storage" / "chat").resolve()
MAX_CHAT_FILE = 10 * 1024 * 1024
ALLOWED_CHAT_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".docx", ".xlsx", ".zip", ".txt", ".csv"}


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=10000)


def _project_for_user(db: Session, project_id: int, user: User):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found.")
    if user.id not in (project.client_id, project.freelancer_id):
        raise HTTPException(403, "You are not a participant in this project.")
    other_id = project.freelancer_id if user.id == project.client_id else project.client_id
    if not other_id:
        raise HTTPException(409, "This project does not have both participants assigned.")
    return project, other_id


def _off_platform_reasons(content: str, project: Project | None = None):
    return off_platform_reasons(content)


def _message_data(message: ProjectMessage, viewer_id: int):
    return {
        "id": message.id, "project_id": message.project_id,
        "sender_id": message.sender_id, "recipient_id": message.recipient_id,
        "content": message.content, "off_platform_flag": message.off_platform_flag,
        "warning_reasons": message.warning_reasons.split(",") if message.warning_reasons else [],
        "attachment_name": message.attachment_name,
        "has_attachment": bool(message.attachment_path),
        "policy_warning": ({"title": "Keep project communication and payments on Aurevo", "message": "This message may move communication or payment off-platform. If you use external channels or direct payment, Aurevo cannot preserve its platform payment records, dispute evidence, or payment support. Keep agreed scope, milestone changes, submissions, and payments in the platform.", "reasons": message.warning_reasons.split(",") if message.warning_reasons else [], "paypal_notice": "PayPal authorization and capture are processed through the configured PayPal account; Aurevo is not an escrow service."} if message.off_platform_flag else None),
        "is_read": message.is_read, "created_at": message.created_at,
        "is_mine": message.sender_id == viewer_id,
    }

@router.get("/api/v1/projects/{project_id}/messages")
def list_messages(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _project_for_user(db, project_id, user)
    messages = db.query(ProjectMessage).filter(ProjectMessage.project_id == project_id).order_by(ProjectMessage.created_at.asc()).all()
    unread = [m for m in messages if m.recipient_id == user.id and not m.is_read]
    for message in unread:
        message.is_read = True
    if unread:
        db.commit()
    return [_message_data(m, user.id) for m in messages]

@router.post("/api/v1/projects/{project_id}/messages")
def send_message(project_id: int, payload: MessageCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    project, recipient_id = _project_for_user(db, project_id, user)
    reasons = _off_platform_reasons(payload.content, project)
    message = ProjectMessage(project_id=project.id, sender_id=user.id, recipient_id=recipient_id,
        content=payload.content.strip(), off_platform_flag=bool(reasons), warning_reasons=",".join(reasons) or None)
    db.add(message)
    db.add(Notification(user_id=recipient_id, title="New project message", message=f"{user.full_name} sent you a message in '{project.title}'."))
    db.commit(); db.refresh(message)
    result = _message_data(message, user.id)
    if reasons:
        result["policy_warning"] = {
            "title": "Keep project communication and payments on Aurevo",
            "message": "This message may move communication or payment off-platform. If you use external channels or direct payment, Aurevo cannot preserve its platform payment records, dispute evidence, or payment support. Keep agreed scope, milestone changes, submissions, and payments in the platform.",
            "reasons": reasons,
            "paypal_notice": "PayPal authorization and capture are processed through the configured PayPal account; Aurevo is not an escrow service.",
        }
    return result

@router.post("/api/v1/projects/{project_id}/messages/attachment")
async def send_attachment(project_id: int, content: str = Form("Shared a file."), file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    project, recipient_id = _project_for_user(db, project_id, user)
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_CHAT_EXTENSIONS:
        raise HTTPException(415, "Unsupported attachment type.")
    data = await file.read(MAX_CHAT_FILE + 1)
    if not data or len(data) > MAX_CHAT_FILE:
        raise HTTPException(413, "Attachment must be between 1 byte and 10 MB.")
    if not validate_file_content(file.filename or "", data):
        raise HTTPException(415, "Attachment content does not match its file extension or is not valid UTF-8 text.")
    CHAT_STORAGE.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}{ext}"
    path = CHAT_STORAGE / name
    path.write_bytes(data)
    reasons = _off_platform_reasons(content, project)
    message = ProjectMessage(project_id=project.id, sender_id=user.id, recipient_id=recipient_id,
        content=content[:10000], off_platform_flag=bool(reasons), warning_reasons=",".join(reasons) or None,
        attachment_name=Path(file.filename or name).name, attachment_path=str(path), attachment_mime=file.content_type)
    db.add(message)
    db.add(Notification(user_id=recipient_id, title="Project attachment received", message=f"{user.full_name} shared a file in '{project.title}'."))
    try:
        db.commit()
        db.refresh(message)
    except Exception:
        db.rollback()
        path.unlink(missing_ok=True)
        raise
    return _message_data(message, user.id)

@router.get("/api/v1/projects/{project_id}/messages/{message_id}/attachment")
def download_attachment(project_id: int, message_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _project_for_user(db, project_id, user)
    message = db.query(ProjectMessage).filter(ProjectMessage.id == message_id, ProjectMessage.project_id == project_id).first()
    if not message or not message.attachment_path:
        raise HTTPException(404, "Attachment not found.")
    path = Path(message.attachment_path).resolve()
    if path.parent != CHAT_STORAGE or not path.is_file():
        raise HTTPException(404, "Attachment is unavailable.")
    return FileResponse(path, filename=message.attachment_name or path.name, media_type=message.attachment_mime or "application/octet-stream")

@router.get("/api/v1/projects/{project_id}/messages/unread-count")
def unread_count(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _project_for_user(db, project_id, user)
    count = db.query(ProjectMessage).filter(ProjectMessage.project_id == project_id, ProjectMessage.recipient_id == user.id, ProjectMessage.is_read.is_(False)).count()
    return {"unread_count": count}
