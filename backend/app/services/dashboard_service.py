from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.project import Project
from app.models.application import Application
from app.models.milestone import Milestone
from app.models.paypal_payment import PayPalPayment
from app.models.notification import Notification
from app.models.activity import Activity


def money(value):
    return Decimal(str(value or 0)).quantize(Decimal("0.01"))


def paypal_currency_totals(query, status):
    rows = query.filter(PayPalPayment.payment_status == status).with_entities(
        PayPalPayment.currency, func.sum(PayPalPayment.amount)
    ).group_by(PayPalPayment.currency).all()
    return [{"currency": currency, "amount": str(money(amount))} for currency, amount in rows]


def serialize_payment(payment):
    return {
        "id": payment.id,
        "milestone_id": payment.milestone_id,
        "project_id": payment.project_id,
        "amount": str(money(payment.amount)),
        "currency": payment.currency,
        "status": payment.payment_status,
        "authorization_status": payment.authorization_status,
        "capture_status": payment.capture_status,
        "authorization_expires_at": payment.authorization_expires_at.isoformat() if payment.authorization_expires_at else None,
        "capture_id": payment.capture_id,
        "captured_at": payment.captured_at.isoformat() if payment.captured_at else None,
        "created_at": payment.created_at.isoformat() if payment.created_at else None,
    }


def serialize_notification(notification):
    return {"id": notification.id, "title": notification.title, "message": notification.message,
            "is_read": bool(notification.is_read), "created_at": notification.created_at.isoformat() if notification.created_at else None}


def serialize_activity(activity):
    return {"id": activity.id, "title": activity.title, "description": activity.description,
            "project_id": activity.project_id, "project_title": activity.project.title,
            "actor_name": activity.actor.full_name if activity.actor else None,
            "created_at": activity.created_at.isoformat() if activity.created_at else None}


def serialize_milestone(milestone, latest_payment=None):
    return {
        "id": milestone.id, "project_id": milestone.project_id, "title": milestone.title,
        "description": milestone.description, "amount": str(money(milestone.amount)),
        "currency": milestone.currency, "status": milestone.status,
        "progress_percentage": milestone.progress_percentage,
        "due_date": milestone.due_date.isoformat() if milestone.due_date else None,
        "submitted_at": milestone.submitted_at.isoformat() if milestone.submitted_at else None,
        "review_deadline": milestone.review_deadline.isoformat() if milestone.review_deadline else None,
        "payment_status": latest_payment.payment_status if latest_payment else None,
        "authorization_expires_at": latest_payment.authorization_expires_at.isoformat() if latest_payment and latest_payment.authorization_expires_at else None,
    }


def get_recent_activity(db, project_ids):
    if not project_ids: return []
    activities = db.query(Activity).filter(Activity.project_id.in_(project_ids)).order_by(Activity.created_at.desc()).limit(5).all()
    return [serialize_activity(activity) for activity in activities]


def get_upcoming_deadlines(db, project_ids):
    if not project_ids: return []
    now = datetime.now(timezone.utc)
    milestones = db.query(Milestone).filter(
        Milestone.project_id.in_(project_ids), Milestone.is_current.is_(True),
        Milestone.due_date >= now, Milestone.status.notin_(["paid", "cancelled", "disputed"]),
    ).order_by(Milestone.due_date.asc()).limit(5).all()
    return [{"id": m.id, "title": m.title, "project_id": m.project_id,
             "due_date": m.due_date.isoformat() if m.due_date else None, "status": m.status} for m in milestones]


def get_notifications(db, user_id):
    rows = db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.created_at.desc()).limit(5).all()
    return [serialize_notification(n) for n in rows]


def _project_ids(query):
    return [row[0] for row in query.with_entities(Project.id).all()]


def _milestones_for_dashboard(db, project_ids):
    if not project_ids: return []
    rows = db.query(Milestone).filter(Milestone.project_id.in_(project_ids), Milestone.is_current.is_(True)).order_by(Milestone.due_date.asc().nullslast(), Milestone.id.asc()).all()
    payments = db.query(PayPalPayment).filter(PayPalPayment.milestone_id.in_([m.id for m in rows])).order_by(PayPalPayment.created_at.desc()).all() if rows else []
    latest = {}
    for payment in payments:
        latest.setdefault(payment.milestone_id, payment)
    return [serialize_milestone(m, latest.get(m.id)) for m in rows]


def get_client_dashboard(db: Session, user_id: int):
    projects = db.query(Project).filter(Project.client_id == user_id)
    project_ids = _project_ids(projects)
    total_projects = projects.count()
    active_projects = projects.filter(Project.status.in_(["active", "in_progress"])).count()
    completed_projects = projects.filter(Project.status == "completed").count()
    pending_applications = db.query(Application).join(Project, Application.project_id == Project.id).filter(Project.client_id == user_id, Application.status == "pending").count()
    milestone_query = db.query(Milestone).filter(Milestone.project_id.in_(project_ids), Milestone.is_current.is_(True)) if project_ids else None
    awaiting_submission = milestone_query.filter(Milestone.status.in_(["not_started", "in_progress", "revision_requested"])).count() if milestone_query is not None else 0
    awaiting_approval = milestone_query.filter(Milestone.status.in_(["submitted", "under_review"])).count() if milestone_query is not None else 0
    payments = db.query(PayPalPayment).filter(PayPalPayment.client_user_id == user_id)
    authorized = paypal_currency_totals(payments, "AUTHORIZED")
    captured = paypal_currency_totals(payments, "CAPTURED")
    pending_count = payments.filter(PayPalPayment.payment_status.in_(["PENDING", "AUTHORIZED"])).count()
    recent = payments.order_by(PayPalPayment.created_at.desc()).limit(5).all()
    return {
        "role": "client",
        "stats": {"total_projects": total_projects, "active_projects": active_projects, "completed_projects": completed_projects,
                  "pending_applications": pending_applications, "total_authorized": authorized, "total_captured": captured,
                  "pending_milestone_payments": pending_count, "awaiting_submission": awaiting_submission, "awaiting_approval": awaiting_approval},
        "milestones": _milestones_for_dashboard(db, project_ids),
        "recent_transactions": [serialize_payment(p) for p in recent],
        "recent_activity": get_recent_activity(db, project_ids),
        "upcoming_deadlines": get_upcoming_deadlines(db, project_ids),
        "notifications": get_notifications(db, user_id),
    }


def get_freelancer_dashboard(db: Session, user_id: int):
    applications = db.query(Application).filter(Application.freelancer_id == user_id)
    projects = db.query(Project).filter(Project.freelancer_id == user_id)
    project_ids = _project_ids(projects)
    total_applications = applications.count()
    pending_applications = applications.filter(Application.status == "pending").count()
    active_projects = projects.filter(Project.status.in_(["active", "in_progress"])).count()
    completed_projects = projects.filter(Project.status == "completed").count()
    milestone_query = db.query(Milestone).filter(Milestone.project_id.in_(project_ids), Milestone.is_current.is_(True)) if project_ids else None
    pending_submissions = milestone_query.filter(Milestone.status.in_(["not_started", "in_progress", "revision_requested"])).count() if milestone_query is not None else 0
    awaiting_approval = milestone_query.filter(Milestone.status.in_(["submitted", "under_review"])).count() if milestone_query is not None else 0
    payments = db.query(PayPalPayment).filter(PayPalPayment.freelancer_user_id == user_id)
    earnings = paypal_currency_totals(payments, "CAPTURED")
    pending_count = payments.filter(PayPalPayment.payment_status.in_(["PENDING", "AUTHORIZED"])).count()
    recent = payments.order_by(PayPalPayment.created_at.desc()).limit(5).all()
    return {
        "role": "freelancer",
        "stats": {"total_applications": total_applications, "pending_applications": pending_applications,
                  "active_projects": active_projects, "completed_projects": completed_projects,
                  "pending_submissions": pending_submissions, "earnings_received": earnings,
                  "payments_awaiting_approval": awaiting_approval, "pending_milestone_payments": pending_count},
        "milestones": _milestones_for_dashboard(db, project_ids),
        "recent_transactions": [serialize_payment(p) for p in recent],
        "recent_activity": get_recent_activity(db, project_ids),
        "upcoming_deadlines": get_upcoming_deadlines(db, project_ids),
        "notifications": get_notifications(db, user_id),
    }
