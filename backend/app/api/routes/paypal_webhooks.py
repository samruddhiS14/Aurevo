from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from sqlalchemy.exc import IntegrityError
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.paypal_payment import PayPalPayment
from app.models.paypal_webhook_event import PayPalWebhookEvent
from app.models.milestone import Milestone
from app.services.paypal_service import PayPalService, PayPalError
from app.services.payment_quote import get_paypal_quote, PaymentQuoteError

router = APIRouter(prefix="/payments/webhooks", tags=["PayPal Webhooks"])


def _money_matches(resource_amount, payment):
    try:
        expected_amount, expected_currency = get_paypal_quote(payment)
        return (
            resource_amount.get("currency_code") == expected_currency
            and Decimal(str(resource_amount.get("value", "0"))) == expected_amount
        )
    except (InvalidOperation, TypeError, ValueError, PaymentQuoteError):
        return False


@router.post("/paypal")
async def paypal_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        event = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON webhook payload.")
    event_id = event.get("id")
    event_type = event.get("event_type")
    resource = event.get("resource") or {}
    resource_id = resource.get("id")
    if not event_id or not event_type or not isinstance(resource, dict):
        raise HTTPException(400, "Invalid PayPal webhook payload.")

    existing = db.query(PayPalWebhookEvent).filter(PayPalWebhookEvent.event_id == event_id).with_for_update().first()
    if existing and existing.processed in ("PROCESSED", "REJECTED"):
        return {"received": True, "duplicate": True, "processed": existing.processed == "PROCESSED"}

    # Verify before persisting the event ID to prevent invalid requests from poisoning deduplication.
    try:
        paypal = PayPalService()
    except PayPalError as exc:
        raise HTTPException(503, str(exc))
    headers = {key.lower(): value for key, value in request.headers.items()}
    try:
        verified = await paypal.verify_webhook(headers, event)
    except Exception:
        raise HTTPException(502, "PayPal webhook verification service is unavailable.")
    if not verified:
        raise HTTPException(400, "Invalid PayPal webhook signature.")

    if existing:
        record = existing
        record.payload = event
        record.processing_error = None
    else:
        record = PayPalWebhookEvent(event_id=event_id, event_type=event_type, resource_id=resource_id, payload=event, processed="RECEIVED")
        db.add(record)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            return {"received": True, "duplicate": True, "processed": False}

    payment = None
    if event_type.startswith("PAYMENT.AUTHORIZATION."):
        payment = db.query(PayPalPayment).filter(PayPalPayment.authorization_id == resource_id).with_for_update().first()
        if not payment:
            related_order = (resource.get("supplementary_data") or {}).get("related_ids", {}).get("order_id")
            if related_order:
                payment = db.query(PayPalPayment).filter(PayPalPayment.paypal_order_id == related_order).with_for_update().first()
    elif event_type.startswith("PAYMENT.CAPTURE."):
        payment = db.query(PayPalPayment).filter(PayPalPayment.capture_id == resource_id).with_for_update().first()
        if not payment:
            authorization_id = (resource.get("supplementary_data") or {}).get("related_ids", {}).get("authorization_id")
            if authorization_id:
                payment = db.query(PayPalPayment).filter(PayPalPayment.authorization_id == authorization_id).with_for_update().first()
    elif event_type.startswith("CHECKOUT.ORDER."):
        payment = db.query(PayPalPayment).filter(PayPalPayment.paypal_order_id == resource_id).with_for_update().first()

    if not payment:
        record.processed = "RECEIVED"
        record.processing_error = "Verified event is awaiting a matching local payment record; retry reconciliation."
        db.commit()
        # Return a retryable status so PayPal redelivers after the local order/authorization transaction commits.
        raise HTTPException(503, "Verified event stored; no matching local payment exists yet. PayPal should retry delivery.")

    if event_type == "PAYMENT.AUTHORIZATION.CREATED":
        if not _money_matches(resource.get("amount") or {}, payment):
            payment.payment_status = "RECONCILIATION_REQUIRED"
            payment.capture_status = "RECONCILIATION_REQUIRED"
            payment.failure_reason = "Verified authorization amount or currency did not match the saved PayPal quote."
            record.processed = "RECONCILIATION_REQUIRED"
            record.processing_error = payment.failure_reason
        elif payment.payment_status not in ("CAPTURED", "VOIDED", "EXPIRED"):
            payment.authorization_status = resource.get("status", "CREATED")
            payment.authorization_id = resource_id
            expiry = resource.get("expiration_time")
            if expiry:
                payment.authorization_expires_at = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
            payment.authorized_at = payment.authorized_at or datetime.now(timezone.utc)
            payment.payment_status = "AUTHORIZED"
            record.processed = "PROCESSED"

    elif event_type == "PAYMENT.AUTHORIZATION.VOIDED":
        if payment.payment_status != "CAPTURED":
            payment.authorization_status = "VOIDED"
            payment.payment_status = "VOIDED"
        record.processed = "PROCESSED"

    elif event_type == "PAYMENT.AUTHORIZATION.DENIED":
        if payment.payment_status != "CAPTURED":
            payment.authorization_status = "DENIED"
            payment.payment_status = "FAILED"
        record.processed = "PROCESSED"

    elif event_type == "PAYMENT.CAPTURE.COMPLETED":
        if not _money_matches(resource.get("amount") or {}, payment):
            payment.capture_status = "RECONCILIATION_REQUIRED"
            payment.payment_status = "RECONCILIATION_REQUIRED"
            payment.failure_reason = "Verified webhook amount/currency mismatch."
            record.processed = "RECONCILIATION_REQUIRED"
            record.processing_error = payment.failure_reason
        else:
            payment.capture_id = resource_id
            payment.capture_status = "COMPLETED"
            payment.authorization_status = "CAPTURED"
            payment.payment_status = "CAPTURED"
            payment.captured_at = datetime.now(timezone.utc)
            milestone = db.get(Milestone, payment.milestone_id)
            if milestone and milestone.status == "approved":
                milestone.status = "paid"
                milestone.completed_at = datetime.now(timezone.utc)
                from app.models import Project
                project = db.get(Project, milestone.project_id)
                if project:
                    remaining = db.query(Milestone).filter(Milestone.project_id == project.id, Milestone.is_current.is_(True), Milestone.status != "paid").count()
                    if remaining == 0:
                        project.status = "completed"
            record.processed = "PROCESSED"

    elif event_type == "PAYMENT.CAPTURE.DENIED":
        if payment.payment_status != "CAPTURED":
            payment.capture_status = "RECONCILIATION_REQUIRED"
            payment.payment_status = "RECONCILIATION_REQUIRED"
            payment.failure_reason = "PayPal reported capture denied."
        record.processed = "PROCESSED"

    elif event_type == "CHECKOUT.ORDER.APPROVED":
        payment.order_status = "APPROVED"
        record.processed = "PROCESSED"

    elif event_type == "CHECKOUT.ORDER.VOIDED":
        if payment.payment_status not in ("CAPTURED", "AUTHORIZED"):
            payment.order_status = "VOIDED"
            payment.payment_status = "VOIDED"
        record.processed = "PROCESSED"
    else:
        record.processed = "PROCESSED"

    if record.processed == "PROCESSED":
        record.processed_at = datetime.now(timezone.utc)
    db.commit()
    return {"received": True, "processed": record.processed == "PROCESSED", "reconciliation_required": record.processed == "RECONCILIATION_REQUIRED"}
