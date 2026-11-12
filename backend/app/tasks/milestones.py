import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from app.celery_app import celery_app
from app.core.config import settings
from app.core.database import SessionLocal
from app.models import Milestone, Project, PayPalPayment, Notification, MilestoneAudit, Dispute, MilestoneReminder, Agreement, AgreementVersion
from app.services.paypal_service import PayPalService
from app.services.payment_quote import get_paypal_quote, PaymentQuoteError


def _utcnow():
    return datetime.now(timezone.utc)


def _notify(db, user_id, title, message):
    if user_id:
        db.add(Notification(user_id=user_id, title=title, message=message))


def _reminder_already_sent(db, milestone_id, submitted_at, offset_minutes):
    return db.query(MilestoneReminder).filter(
        MilestoneReminder.milestone_id == milestone_id,
        MilestoneReminder.submission_at == submitted_at,
        MilestoneReminder.reminder_offset_minutes == offset_minutes,
    ).first() is not None


def _send_reminder_in_session(db, milestone, offset_minutes):
    submitted_at = milestone.submitted_at
    if not submitted_at or _reminder_already_sent(db, milestone.id, submitted_at, offset_minutes):
        return False
    project = db.get(Project, milestone.project_id)
    if not project:
        return False
    offset_label = f"{offset_minutes} minutes" if offset_minutes < 60 else f"{offset_minutes // 60} hours"
    db.add(MilestoneReminder(milestone_id=milestone.id, submission_at=submitted_at, reminder_offset_minutes=offset_minutes))
    _notify(db, project.client_id, "Milestone review reminder", f"'{milestone.title}' was submitted {offset_label} ago. Please review the deliverables, request revisions, or raise a dispute before the review deadline.")
    return True


@celery_app.task(name="app.tasks.milestones.send_review_reminder")
def send_review_reminder(milestone_id: int, expected_submission_at: str, offset_minutes: int):
    db = SessionLocal()
    try:
        milestone = db.query(Milestone).filter(Milestone.id == milestone_id).with_for_update().first()
        if not milestone or milestone.status not in ("submitted", "under_review"):
            return {"sent": False, "reason": "milestone_not_waiting"}
        if not milestone.submitted_at or milestone.submitted_at.isoformat() != expected_submission_at:
            return {"sent": False, "reason": "submission_changed"}
        if not _send_reminder_in_session(db, milestone, offset_minutes):
            return {"sent": False, "reason": "already_sent_or_missing_project"}
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            return {"sent": False, "reason": "duplicate_delivery"}
        return {"sent": True}
    finally:
        db.close()


async def _capture_authorized(payment):
    amount, currency = get_paypal_quote(payment)
    service = PayPalService()
    return await service.capture_authorization(
        payment.authorization_id,
        amount,
        currency,
        payment.capture_request_id,
    )


def _mark_review_window_blocked(db, milestone, reason):
    submitted_at = milestone.submitted_at
    if not submitted_at or _reminder_already_sent(db, milestone.id, submitted_at, -1):
        return
    db.add(MilestoneReminder(milestone_id=milestone.id, submission_at=submitted_at, reminder_offset_minutes=-1))
    project = db.get(Project, milestone.project_id)
    if project:
        message = f"The automatic 72-hour review process for '{milestone.title}' could not capture payment: {reason}. No payment was captured. Please review the milestone and resolve the payment status manually."
        _notify(db, project.client_id, "Automatic milestone capture needs attention", message)
        _notify(db, project.freelancer_id, "Automatic milestone capture needs attention", message)


def _auto_approve_one(db, milestone):
    now = _utcnow()
    if milestone.status not in ("submitted", "under_review") or not milestone.review_deadline:
        return "not_waiting"
    deadline = milestone.review_deadline
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    if deadline > now:
        return "not_due"
    if db.query(Dispute).filter(Dispute.milestone_id == milestone.id, Dispute.status.in_(("open", "under_review"))).first():
        return "disputed"

    agreement = db.query(Agreement).filter(Agreement.project_id == milestone.project_id).first()
    version = db.get(AgreementVersion, agreement.active_version_id) if agreement and agreement.active_version_id else None
    if not version or agreement.active_version_id != milestone.agreement_version_id or version.status != "active" or not version.client_approved or not version.freelancer_approved:
        _mark_review_window_blocked(db, milestone, "the milestone no longer matches the mutually approved active agreement")
        db.commit()
        return "agreement_not_active"

    payment = db.query(PayPalPayment).filter(PayPalPayment.milestone_id == milestone.id).order_by(PayPalPayment.created_at.desc()).with_for_update().first()
    if not payment or payment.payment_status != "AUTHORIZED" or not payment.authorization_id:
        _mark_review_window_blocked(db, milestone, "no active PayPal authorization was found")
        db.commit()
        return "no_active_authorization"
    try:
        expected_paypal_amount, expected_paypal_currency = get_paypal_quote(payment)
    except PaymentQuoteError:
        payment.payment_status = "RECONCILIATION_REQUIRED"
        payment.capture_status = "RECONCILIATION_REQUIRED"
        payment.failure_reason = "Automatic capture blocked because the saved PayPal quote is incomplete."
        _mark_review_window_blocked(db, milestone, "the saved PayPal currency quote is incomplete")
        db.commit()
        return "quote_reconciliation_required"
    expiry = payment.authorization_expires_at
    if not expiry:
        _mark_review_window_blocked(db, milestone, "the PayPal authorization expiry timestamp is missing")
        db.commit()
        return "missing_expiry"
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)
    if expiry <= now:
        payment.payment_status = "EXPIRED"
        payment.authorization_status = "EXPIRED"
        payment.failure_reason = "Authorization expired before automatic review completion."
        _mark_review_window_blocked(db, milestone, "the PayPal authorization has expired")
        db.commit()
        return "authorization_expired"

    old_status = milestone.status
    milestone.status = "approved"
    milestone.approved_at = now
    milestone.revision_explanation = None
    db.add(MilestoneAudit(milestone_id=milestone.id, actor_user_id=None, previous_status=old_status, new_status="approved", description="Automatically approved after the configured client review window elapsed.", details={"automatic": True, "review_deadline": deadline.isoformat()}))
    db.flush()
    try:
        result = asyncio.run(_capture_authorized(payment))
        amount = result.get("amount", {})
        if result.get("status") != "COMPLETED" or amount.get("currency_code") != expected_paypal_currency or Decimal(amount.get("value", "0")) != expected_paypal_amount:
            payment.capture_status = "RECONCILIATION_REQUIRED"
            payment.payment_status = "RECONCILIATION_REQUIRED"
            payment.failure_reason = "Automatic capture response did not match the authorized amount/currency."
            payment.paypal_response = result
            _mark_review_window_blocked(db, milestone, "PayPal returned an amount/status requiring reconciliation")
            db.commit()
            return "capture_reconciliation_required"
        payment.capture_id = result.get("id")
        payment.capture_status = "COMPLETED"
        payment.authorization_status = "CAPTURED"
        payment.payment_status = "CAPTURED"
        payment.captured_at = now
        payment.paypal_response = result
        milestone.status = "paid"
        milestone.completed_at = now
        project = db.get(Project, milestone.project_id)
        if project:
            remaining = db.query(Milestone).filter(Milestone.project_id == project.id, Milestone.is_current.is_(True), Milestone.status != "paid").count()
            if remaining == 0:
                project.status = "completed"
            _notify(db, project.client_id, "Milestone auto-approved and paid", f"'{milestone.title}' passed its review deadline and PayPal confirmed capture.")
            _notify(db, project.freelancer_id, "Milestone auto-approved and paid", f"'{milestone.title}' passed its review deadline and PayPal confirmed capture.")
        db.add(MilestoneAudit(milestone_id=milestone.id, actor_user_id=None, previous_status="approved", new_status="paid", description="PayPal confirmed automatic milestone capture.", details={"capture_id": payment.capture_id, "amount": str(payment.amount), "currency": payment.currency}))
        db.commit()
        return "captured"
    except Exception as exc:
        db.rollback()
        payment = db.query(PayPalPayment).filter(PayPalPayment.id == payment.id).with_for_update().first()
        milestone = db.query(Milestone).filter(Milestone.id == milestone.id).with_for_update().first()
        if payment:
            payment.capture_status = "RECONCILIATION_REQUIRED"
            payment.payment_status = "RECONCILIATION_REQUIRED"
            payment.failure_reason = f"Automatic capture result is uncertain: {type(exc).__name__}"
            if milestone:
                _mark_review_window_blocked(db, milestone, "PayPal capture result is uncertain; reconciliation is required")
            db.commit()
        return "capture_uncertain"


@celery_app.task(name="app.tasks.milestones.auto_approve_milestone")
def auto_approve_milestone(milestone_id: int, expected_submission_at: str):
    db = SessionLocal()
    try:
        milestone = db.query(Milestone).filter(Milestone.id == milestone_id).with_for_update().first()
        if not milestone or not milestone.submitted_at or milestone.submitted_at.isoformat() != expected_submission_at:
            return {"processed": False, "reason": "submission_changed_or_missing"}
        outcome = _auto_approve_one(db, milestone)
        return {"processed": outcome not in ("not_due", "not_waiting"), "outcome": outcome}
    finally:
        db.close()


@celery_app.task(name="app.tasks.milestones.process_review_reminders")
def process_review_reminders():
    db = SessionLocal()
    sent = 0
    try:
        if settings.MILESTONE_REMINDER_MINUTES.strip():
            offsets = [int(x.strip()) for x in settings.MILESTONE_REMINDER_MINUTES.split(",") if x.strip()]
        else:
            offsets = [int(x.strip()) * 60 for x in settings.MILESTONE_REMINDER_HOURS.split(",") if x.strip()]
        now = _utcnow()
        rows = db.query(Milestone).filter(Milestone.status.in_(("submitted", "under_review")), Milestone.submitted_at.is_not(None)).with_for_update(skip_locked=True).all()
        for milestone in rows:
            submitted_at = milestone.submitted_at
            if submitted_at.tzinfo is None:
                submitted_at = submitted_at.replace(tzinfo=timezone.utc)
            elapsed_minutes = int((now - submitted_at).total_seconds() // 60)
            for offset in offsets:
                review_minutes = settings.MILESTONE_REVIEW_MINUTES or settings.MILESTONE_REVIEW_HOURS * 60
                if 0 < offset < review_minutes and elapsed_minutes >= offset:
                    if _send_reminder_in_session(db, milestone, offset):
                        sent += 1
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
        return {"reminders_sent": sent}
    finally:
        db.close()


@celery_app.task(name="app.tasks.milestones.process_overdue_reviews")
def process_overdue_reviews():
    db = SessionLocal()
    results = {}
    try:
        due = db.query(Milestone).filter(Milestone.status.in_(("submitted", "under_review")), Milestone.review_deadline.is_not(None), Milestone.review_deadline <= _utcnow()).with_for_update(skip_locked=True).all()
        for milestone in due:
            outcome = _auto_approve_one(db, milestone)
            results[outcome] = results.get(outcome, 0) + 1
        return results
    finally:
        db.close()
