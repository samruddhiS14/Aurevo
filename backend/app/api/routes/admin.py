from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.routes.auth import require_role
from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.project import Project
from app.models.dispute import Dispute
from app.models.paypal_payment import PayPalPayment
from app.models.project_message import ProjectMessage
from app.models.paypal_webhook_event import PayPalWebhookEvent
from app.models.activity import Activity

router = APIRouter(prefix="/admin", tags=["Admin"] )
admin_only = require_role(UserRole.ADMIN)


def _page(query, page: int, page_size: int):
    total = query.count()
    rows = query.offset((page - 1) * page_size).limit(page_size).all()
    return total, rows


@router.get("/dashboard")
def admin_dashboard(db: Session = Depends(get_db), _: User = Depends(admin_only)):
    return {
        "users": db.query(func.count(User.id)).scalar() or 0,
        "clients": db.query(func.count(User.id)).filter(User.role == UserRole.CLIENT).scalar() or 0,
        "freelancers": db.query(func.count(User.id)).filter(User.role == UserRole.FREELANCER).scalar() or 0,
        "projects": db.query(func.count(Project.id)).scalar() or 0,
        "open_disputes": db.query(func.count(Dispute.id)).filter(Dispute.status.in_(["open", "under_review", "awaiting_response"])).scalar() or 0,
        "payments": db.query(func.count(PayPalPayment.id)).scalar() or 0,
        "flagged_messages": db.query(func.count(ProjectMessage.id)).filter(ProjectMessage.off_platform_flag.is_(True)).scalar() or 0,
        "unprocessed_webhooks": db.query(func.count(PayPalWebhookEvent.id)).filter(PayPalWebhookEvent.processed != "PROCESSED").scalar() or 0,
    }


@router.get("/users")
def list_users(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), db: Session = Depends(get_db), _: User = Depends(admin_only)):
    total, rows = _page(db.query(User).order_by(User.created_at.desc()), page, page_size)
    return {"total": total, "page": page, "page_size": page_size, "items": [{"id": u.id, "full_name": u.full_name, "email": u.email, "role": u.role.value, "country": u.country, "is_active": u.is_active, "created_at": u.created_at} for u in rows]}


@router.patch("/users/{user_id}/active")
def set_user_active(user_id: int, active: bool, db: Session = Depends(get_db), current: User = Depends(admin_only)):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == current.id:
        raise HTTPException(status_code=400, detail="You cannot deactivate your own admin account")
    if target.role == UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin accounts cannot be changed from this screen")
    target.is_active = active
    target.token_version = (target.token_version or 0) + 1
    db.commit()
    return {"id": target.id, "is_active": target.is_active}


@router.get("/projects")
def list_projects(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), db: Session = Depends(get_db), _: User = Depends(admin_only)):
    total, rows = _page(db.query(Project).order_by(Project.created_at.desc()), page, page_size)
    return {"total": total, "page": page, "page_size": page_size, "items": [{"id": p.id, "title": p.title, "status": p.status, "client_id": p.client_id, "freelancer_id": p.freelancer_id, "budget": str(p.budget) if p.budget is not None else None, "currency": p.currency, "created_at": p.created_at} for p in rows]}


@router.get("/disputes")
def list_disputes(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), db: Session = Depends(get_db), _: User = Depends(admin_only)):
    total, rows = _page(db.query(Dispute).order_by(Dispute.created_at.desc()), page, page_size)
    return {"total": total, "page": page, "page_size": page_size, "items": [{"id": d.id, "project_id": d.project_id, "milestone_id": d.milestone_id, "status": d.status, "reason": d.reason, "created_at": d.created_at} for d in rows]}


@router.get("/payments")
def list_payments(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), db: Session = Depends(get_db), _: User = Depends(admin_only)):
    total, rows = _page(db.query(PayPalPayment).order_by(PayPalPayment.created_at.desc()), page, page_size)
    return {"total": total, "page": page, "page_size": page_size, "items": [{"id": p.id, "project_id": p.project_id, "milestone_id": p.milestone_id, "client_user_id": p.client_user_id, "freelancer_user_id": p.freelancer_user_id, "amount": str(p.amount), "currency": p.currency, "paypal_amount": str(p.paypal_amount) if p.paypal_amount is not None else None, "paypal_currency": p.paypal_currency, "exchange_rate": str(p.exchange_rate) if p.exchange_rate is not None else None, "exchange_rate_date": p.exchange_rate_date, "status": p.payment_status, "order_status": p.order_status, "authorization_expires_at": p.authorization_expires_at, "failure_reason": p.failure_reason, "created_at": p.created_at} for p in rows]}


@router.get("/detection-logs")
def detection_logs(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), db: Session = Depends(get_db), _: User = Depends(admin_only)):
    query = db.query(ProjectMessage).filter(ProjectMessage.off_platform_flag.is_(True)).order_by(ProjectMessage.created_at.desc())
    total, rows = _page(query, page, page_size)
    return {"total": total, "page": page, "page_size": page_size, "items": [{"id": m.id, "project_id": m.project_id, "sender_id": m.sender_id, "recipient_id": m.recipient_id, "warning_reasons": m.warning_reasons, "created_at": m.created_at} for m in rows]}


@router.get("/webhooks")
def list_webhooks(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), db: Session = Depends(get_db), _: User = Depends(admin_only)):
    total, rows = _page(db.query(PayPalWebhookEvent).order_by(PayPalWebhookEvent.received_at.desc()), page, page_size)
    return {"total": total, "page": page, "page_size": page_size, "items": [{"id": e.id, "event_id": e.event_id, "event_type": e.event_type, "processed": e.processed, "processing_error": e.processing_error, "received_at": e.received_at} for e in rows]}


@router.get("/activity")
def list_activity(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), db: Session = Depends(get_db), _: User = Depends(admin_only)):
    query = db.query(Activity).order_by(Activity.created_at.desc())
    total, rows = _page(query, page, page_size)
    return {"total": total, "page": page, "page_size": page_size, "items": [{"id": a.id, "project_id": a.project_id, "actor_user_id": a.actor_user_id, "title": a.title, "description": a.description, "created_at": a.created_at} for a in rows]}
