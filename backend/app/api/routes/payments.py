from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models.user import User
from app.models.milestone import Milestone
from app.models.project import Project
from app.models.agreement import Agreement, AgreementVersion
from app.models.paypal_payment import PayPalPayment
from app.services.paypal_service import PayPalService, PayPalError
from app.services.agreement_service import get_project_participants
from app.services.exchange_rate_service import create_paypal_quote, ExchangeRateError
from app.services.payment_quote import get_paypal_quote, PaymentQuoteError


router = APIRouter(prefix="/payments", tags=["PayPal Payments"])


def participants(db, project):
    client, freelancer = get_project_participants(db, project)
    return client, freelancer


def verify_client(db, project, user):
    client, _ = participants(db, project)
    if client.id != user.id:
        raise HTTPException(403, "Only the project client can perform this action.")


def verify_participant(db, project, user):
    client, freelancer = participants(db, project)
    if user.id not in (client.id, freelancer.id):
        raise HTTPException(403, "You are not a project participant.")


def verify_active_agreement(db, milestone):
    agreement = db.query(Agreement).filter(
        Agreement.project_id == milestone.project_id
    ).first()

    if not agreement or not agreement.active_version_id:
        raise HTTPException(400, "No active agreement exists.")

    if agreement.active_version_id != milestone.agreement_version_id:
        raise HTTPException(400, "This milestone is not part of the active agreement.")

    version = db.get(AgreementVersion, agreement.active_version_id)

    if not version or version.status != "active":
        raise HTTPException(400, "Agreement is not fully approved.")

    if not version.client_approved or not version.freelancer_approved:
        raise HTTPException(400, "Both parties must approve the agreement.")

    return agreement


def get_milestone_or_404(db, milestone_id):
    milestone = db.query(Milestone).filter(
        Milestone.id == milestone_id,
        Milestone.is_current.is_(True),
    ).with_for_update().first()

    if not milestone:
        raise HTTPException(404, "Current milestone not found.")

    return milestone


@router.post("/milestones/{milestone_id}/create-order")
async def create_milestone_order(
    milestone_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    milestone = get_milestone_or_404(db, milestone_id)
    project = db.get(Project, milestone.project_id)
    verify_client(db, project, current_user)
    verify_active_agreement(db, milestone)

    if milestone.status not in ("not_started", "in_progress", "submitted", "under_review", "approved"):
        raise HTTPException(400, "Payment authorization is not available for this milestone.")

    amount = Decimal(milestone.amount).quantize(Decimal("0.01"))
    if amount <= 0:
        raise HTTPException(400, "Milestone amount must be positive.")

    payment_rows = db.query(PayPalPayment).filter(
        PayPalPayment.milestone_id == milestone.id,
    ).order_by(PayPalPayment.created_at.desc()).with_for_update().all()

    unresolved_payment = next((row for row in payment_rows if row.payment_status == "RECONCILIATION_REQUIRED"), None)
    if unresolved_payment:
        raise HTTPException(409, "A previous payment outcome is unresolved. Reconcile it before creating another PayPal order.")
    active_rows = [row for row in payment_rows if row.payment_status in ("PENDING", "AUTHORIZED")]
    captured_payment = next((row for row in payment_rows if row.payment_status == "CAPTURED"), None)
    if captured_payment and active_rows:
        for row in active_rows:
            row.payment_status = "RECONCILIATION_REQUIRED"
            row.capture_status = "RECONCILIATION_REQUIRED"
            row.failure_reason = "Conflicting historical payment records exist for this milestone."
        db.commit()
        raise HTTPException(409, "Conflicting payment records require reconciliation before another payment can be started.")
    if captured_payment:
        return {"payment_id": captured_payment.id, "status": "CAPTURED", "capture_id": captured_payment.capture_id, "idempotent": True}
    if len(active_rows) > 1:
        for row in active_rows:
            row.payment_status = "RECONCILIATION_REQUIRED"
            row.capture_status = "RECONCILIATION_REQUIRED"
            row.failure_reason = "Multiple active payment records exist for this milestone."
        db.commit()
        raise HTTPException(409, "Multiple active payment records require reconciliation.")
    payment = active_rows[0] if active_rows else None

    if payment and payment.payment_status == "AUTHORIZED":
        try:
            authorized_amount, authorized_currency = get_paypal_quote(payment)
        except PaymentQuoteError as exc:
            payment.payment_status = "RECONCILIATION_REQUIRED"
            payment.capture_status = "RECONCILIATION_REQUIRED"
            payment.failure_reason = "Authorized legacy payment has no complete immutable PayPal quote."
            db.commit()
            raise HTTPException(409, str(exc))
        return {"payment_id": payment.id, "order_id": payment.paypal_order_id, "status": "AUTHORIZED", "authorization_id": payment.authorization_id, "expires_at": payment.authorization_expires_at, "paypal_amount": str(authorized_amount), "paypal_currency": authorized_currency, "idempotent": True}

    try:
        paypal = PayPalService()
    except PayPalError as exc:
        raise HTTPException(503, str(exc))
    if payment and payment.paypal_order_id:
        try:
            get_paypal_quote(payment)
        except PaymentQuoteError as exc:
            payment.payment_status = "RECONCILIATION_REQUIRED"
            payment.capture_status = "RECONCILIATION_REQUIRED"
            payment.failure_reason = "Legacy PayPal order is missing a complete immutable currency quote."
            db.commit()
            raise HTTPException(409, str(exc))
        try:
            prior_order = await paypal.get_order(payment.paypal_order_id)
        except Exception:
            raise HTTPException(502, "Could not retrieve the existing PayPal order. Please retry or contact support if the order remains pending.")
        approval_url = next((link.get("href") for link in prior_order.get("links", []) if link.get("rel") in ("payer-action", "approve")), None)
        if approval_url:
            return {"payment_id": payment.id, "order_id": payment.paypal_order_id, "approval_url": approval_url, "amount": str(payment.amount), "currency": payment.currency, "paypal_amount": str(payment.paypal_amount if payment.paypal_amount is not None else payment.amount), "paypal_currency": payment.paypal_currency or payment.currency, "exchange_rate": str(payment.exchange_rate) if payment.exchange_rate is not None else None, "exchange_rate_date": payment.exchange_rate_date, "status": payment.payment_status, "idempotent": True}
        if prior_order.get("status") == "APPROVED":
            return {"payment_id": payment.id, "order_id": payment.paypal_order_id, "status": "APPROVED", "continue_authorization": True, "idempotent": True}
        raise HTTPException(409, "An active PayPal order exists but has no buyer approval link. Check the order in PayPal Sandbox.")

    if not payment:
        client, freelancer = participants(db, project)
        try:
            quote = await create_paypal_quote(amount, milestone.currency)
        except ExchangeRateError as exc:
            raise HTTPException(503, str(exc), headers={"Retry-After": "60"})
        payment = PayPalPayment(
            milestone_id=milestone.id,
            project_id=project.id,
            client_user_id=client.id,
            freelancer_user_id=freelancer.id,
            amount=quote.original_amount,
            currency=quote.original_currency,
            paypal_amount=quote.paypal_amount,
            paypal_currency=quote.paypal_currency,
            exchange_rate=quote.rate,
            exchange_rate_date=quote.rate_date,
            exchange_rate_source=quote.source,
            exchange_rate_fetched_at=quote.fetched_at,
            create_request_id=str(uuid4()),
            authorize_request_id=str(uuid4()),
            capture_request_id=str(uuid4()),
            payment_status="PENDING",
        )
        db.add(payment)
        db.commit()  # Persist quote and idempotency key before calling PayPal.
        db.refresh(payment)
    elif not payment.paypal_order_id and (payment.paypal_amount is None or not payment.paypal_currency):
        # A legacy pending row without a PayPal order may safely receive its first quote.
        try:
            quote = await create_paypal_quote(Decimal(payment.amount), payment.currency)
        except ExchangeRateError as exc:
            raise HTTPException(503, str(exc), headers={"Retry-After": "60"})
        payment.paypal_amount = quote.paypal_amount
        payment.paypal_currency = quote.paypal_currency
        payment.exchange_rate = quote.rate
        payment.exchange_rate_date = quote.rate_date
        payment.exchange_rate_source = quote.source
        payment.exchange_rate_fetched_at = quote.fetched_at
        db.commit()
        db.refresh(payment)

    paypal_amount = payment.paypal_amount if payment.paypal_amount is not None else payment.amount
    paypal_currency = payment.paypal_currency or payment.currency
    try:
        result = await paypal.create_order(
            milestone, payment.id, payment.create_request_id,
            amount=paypal_amount, currency=paypal_currency,
        )
        payment.paypal_order_id = result["id"]
        payment.order_status = result.get("status", "CREATED")
        payment.paypal_response = result
        approval_url = next((link.get("href") for link in result.get("links", []) if link.get("rel") in ("payer-action", "approve")), None)
        db.commit()
        if not approval_url:
            raise PayPalError("PayPal did not return a buyer approval URL. The order ID has been saved for reconciliation.")
        return {"payment_id": payment.id, "order_id": payment.paypal_order_id, "approval_url": approval_url, "amount": str(payment.amount), "currency": payment.currency, "paypal_amount": str(payment.paypal_amount if payment.paypal_amount is not None else payment.amount), "paypal_currency": payment.paypal_currency or payment.currency, "exchange_rate": str(payment.exchange_rate) if payment.exchange_rate is not None else None, "exchange_rate_date": payment.exchange_rate_date, "status": payment.payment_status}
    except Exception as exc:
        db.rollback()
        # Keep the persisted payment row and request ID so a retry is idempotent.
        failed_payment = db.get(PayPalPayment, payment.id)
        if failed_payment:
            failed_payment.failure_reason = f"Order creation attempt needs retry: {type(exc).__name__}"
            db.commit()
        raise HTTPException(502, "Could not create the PayPal order. The request is saved for a safe retry; check payment history before starting another payment.")


@router.post("/orders/{order_id}/authorize")
async def authorize_milestone_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payment = db.query(PayPalPayment).filter(
        PayPalPayment.paypal_order_id == order_id
    ).with_for_update().first()

    if not payment:
        raise HTTPException(404, "Payment order not found.")

    if payment.client_user_id != current_user.id:
        raise HTTPException(403, "Only the client can authorize this payment.")

    try:
        paypal_amount, paypal_currency = get_paypal_quote(payment)
    except PaymentQuoteError as exc:
        payment.payment_status = "RECONCILIATION_REQUIRED"
        payment.capture_status = "RECONCILIATION_REQUIRED"
        payment.failure_reason = "Authorization blocked because the saved PayPal quote is incomplete."
        db.commit()
        raise HTTPException(409, str(exc))

    if payment.payment_status == "AUTHORIZED":
        return {
            "status": "AUTHORIZED",
            "authorization_id": payment.authorization_id,
            "expires_at": payment.authorization_expires_at,
            "paypal_amount": str(paypal_amount),
            "paypal_currency": paypal_currency,
            "idempotent": True,
        }

    if payment.payment_status != "PENDING":
        raise HTTPException(409, "This payment cannot be authorized.")

    try:
        paypal = PayPalService()

        order = await paypal.get_order(order_id)

        if order.get("status") != "APPROVED":
            raise HTTPException(400, "PayPal order has not been approved.")

        purchase_units = order.get("purchase_units", [])
        if len(purchase_units) != 1:
            raise HTTPException(400, "Unexpected PayPal purchase unit count.")

        order_amount = purchase_units[0].get("amount", {})
        if (
            order_amount.get("currency_code") != paypal_currency
            or Decimal(order_amount.get("value", "0")) != paypal_amount
        ):
            raise HTTPException(400, "PayPal order amount does not match the milestone.")

        result = await paypal.authorize_order(
            order_id,
            payment.authorize_request_id,
        )

        authorization = (
            result.get("purchase_units", [{}])[0]
            .get("payments", {})
            .get("authorizations", [{}])[0]
        )

        if authorization.get("status") not in ("CREATED", "PENDING"):
            raise HTTPException(400, "PayPal authorization was not successful.")

        authorized_amount = authorization.get("amount", {})

        if (
            authorized_amount.get("currency_code") != paypal_currency
            or Decimal(authorized_amount.get("value", "0")) != paypal_amount
        ):
            raise HTTPException(400, "Authorized amount does not match the milestone.")

        expiry = authorization.get("expiration_time")

        if not expiry:
            raise HTTPException(
                502,
                "PayPal did not return an authorization expiry timestamp. "
                "Payment cannot be marked as authorized.",
            )

        payment.authorization_id = authorization["id"]
        payment.authorization_status = authorization["status"]
        payment.authorization_expires_at = datetime.fromisoformat(
            expiry.replace("Z", "+00:00")
        )
        payment.authorized_at = datetime.now(timezone.utc)
        payment.payment_status = "AUTHORIZED"
        payment.paypal_response = result

        db.commit()

        return {
            "status": payment.payment_status,
            "authorization_id": payment.authorization_id,
            "expires_at": payment.authorization_expires_at,
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(502, "PayPal authorization could not be verified. Check payment history before retrying.")


@router.post("/milestones/{milestone_id}/capture")
async def capture_milestone_payment(
    milestone_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    milestone = get_milestone_or_404(db, milestone_id)
    project = db.get(Project, milestone.project_id)

    verify_client(db, project, current_user)

    payment_rows = db.query(PayPalPayment).filter(
        PayPalPayment.milestone_id == milestone.id,
    ).order_by(PayPalPayment.created_at.desc()).with_for_update().all()
    if any(row.payment_status == "RECONCILIATION_REQUIRED" for row in payment_rows):
        raise HTTPException(409, "A previous payment outcome requires reconciliation before capture.")
    authorized_rows = [row for row in payment_rows if row.payment_status == "AUTHORIZED"]
    captured_payment = next((row for row in payment_rows if row.capture_status == "COMPLETED"), None)
    if captured_payment and authorized_rows:
        for row in authorized_rows:
            row.payment_status = "RECONCILIATION_REQUIRED"
            row.capture_status = "RECONCILIATION_REQUIRED"
            row.failure_reason = "A captured payment and an additional active authorization exist for this milestone."
        db.commit()
        raise HTTPException(409, "Multiple payment records exist for this milestone and require reconciliation.")
    if captured_payment:
        return {"status": "CAPTURED", "capture_id": captured_payment.capture_id, "amount": str(captured_payment.amount), "currency": captured_payment.currency, "captured_at": captured_payment.captured_at, "idempotent": True}
    if len(authorized_rows) > 1:
        for row in authorized_rows:
            row.payment_status = "RECONCILIATION_REQUIRED"
            row.capture_status = "RECONCILIATION_REQUIRED"
            row.failure_reason = "Multiple active authorizations exist for this milestone."
        db.commit()
        raise HTTPException(409, "Multiple active authorizations require reconciliation.")
    payment = authorized_rows[0] if authorized_rows else None
    if not payment:
        raise HTTPException(404, "No active authorization exists for this milestone.")

    try:
        paypal_amount, paypal_currency = get_paypal_quote(payment)
    except PaymentQuoteError as exc:
        payment.payment_status = "RECONCILIATION_REQUIRED"
        payment.capture_status = "RECONCILIATION_REQUIRED"
        payment.failure_reason = "Capture blocked because the saved PayPal quote is incomplete."
        db.commit()
        raise HTTPException(409, str(exc))

    verify_active_agreement(db, milestone)

    if milestone.status != "approved":
        raise HTTPException(400, "Client must approve the milestone submission first.")

    if not payment.authorization_expires_at:
        raise HTTPException(400, "Authorization expiry is missing.")

    if datetime.now(timezone.utc) >= payment.authorization_expires_at:
        payment.authorization_status = "EXPIRED"
        payment.payment_status = "EXPIRED"
        db.commit()
        raise HTTPException(409, "Authorization expired. Client must authorize a new payment.")

    if Decimal(payment.amount) != Decimal(milestone.amount) or payment.currency.upper() != milestone.currency.upper():
        raise HTTPException(400, "Original payment quote no longer matches the milestone.")

    try:
        paypal = PayPalService()

        result = await paypal.capture_authorization(
            payment.authorization_id,
            paypal_amount,
            paypal_currency,
            payment.capture_request_id,
        )

        if result.get("status") != "COMPLETED":
            payment.capture_status = "RECONCILIATION_REQUIRED"
            payment.payment_status = "RECONCILIATION_REQUIRED"
            payment.failure_reason = f"PayPal capture returned non-completed status: {result.get('status', 'UNKNOWN')}"
            payment.paypal_response = result
            db.commit()
            raise HTTPException(502, "PayPal has not confirmed successful capture. Payment requires reconciliation.")

        captured_amount = result.get("amount", {})

        if (
            captured_amount.get("currency_code") != paypal_currency
            or Decimal(captured_amount.get("value", "0")) != paypal_amount
        ):
            payment.capture_status = "RECONCILIATION_REQUIRED"
            payment.payment_status = "RECONCILIATION_REQUIRED"
            payment.failure_reason = "Capture amount or currency mismatch."
            payment.paypal_response = result
            db.commit()
            raise HTTPException(502, "Capture requires payment reconciliation.")

        payment.capture_id = result["id"]
        payment.capture_status = "COMPLETED"
        payment.authorization_status = "CAPTURED"
        payment.payment_status = "CAPTURED"
        payment.captured_at = datetime.now(timezone.utc)
        payment.paypal_response = result

        milestone.status = "paid"
        milestone.completed_at = datetime.now(timezone.utc)
        remaining = db.query(Milestone).filter(Milestone.project_id == project.id, Milestone.is_current.is_(True), Milestone.status != "paid").count()
        if remaining == 0:
            project.status = "completed"

        db.commit()

        return {
            "status": "CAPTURED",
            "capture_id": payment.capture_id,
            "amount": str(payment.amount),
            "currency": payment.currency,
            "paypal_amount": str(payment.paypal_amount) if payment.paypal_amount is not None else (str(payment.amount) if payment.currency.upper() == "USD" else None),
            "paypal_currency": payment.paypal_currency or ("USD" if payment.currency.upper() == "USD" else None),
            "exchange_rate": str(payment.exchange_rate) if payment.exchange_rate is not None else None,
            "captured_at": payment.captured_at,
        }

    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        # The remote capture may have succeeded even if the response was lost.
        # Stop automatic retries and require reconciliation rather than risking a second capture.
        uncertain = db.query(PayPalPayment).filter(PayPalPayment.id == payment.id).with_for_update().first()
        if uncertain and uncertain.payment_status != "CAPTURED":
            uncertain.capture_status = "RECONCILIATION_REQUIRED"
            uncertain.payment_status = "RECONCILIATION_REQUIRED"
            uncertain.failure_reason = f"Capture outcome is uncertain: {type(exc).__name__}"
            db.commit()
        raise HTTPException(502, "PayPal capture outcome is uncertain and requires reconciliation. Do not retry until the payment is checked.")


@router.get("/mine")
def get_my_payments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payments = db.query(PayPalPayment).filter(
        (PayPalPayment.client_user_id == current_user.id)
        | (PayPalPayment.freelancer_user_id == current_user.id)
    ).order_by(PayPalPayment.created_at.desc()).all()

    return [
        {
            "id": payment.id,
            "milestone_id": payment.milestone_id,
            "milestone_title": payment.milestone.title if payment.milestone else None,
            "project_id": payment.project_id,
            "project_title": payment.project.title if payment.project else None,
            "amount": str(payment.amount),
            "currency": payment.currency,
            "paypal_amount": str(payment.paypal_amount) if payment.paypal_amount is not None else (str(payment.amount) if payment.currency.upper() == "USD" else None),
            "paypal_currency": payment.paypal_currency or ("USD" if payment.currency.upper() == "USD" else None),
            "exchange_rate": str(payment.exchange_rate) if payment.exchange_rate is not None else None,
            "exchange_rate_date": payment.exchange_rate_date,
            "status": payment.payment_status,
            "payment_status": payment.payment_status,
            "authorization_status": payment.authorization_status,
            "capture_status": payment.capture_status,
            "failure_reason": payment.failure_reason,
            "authorization_expires_at": payment.authorization_expires_at,
            "capture_id": payment.capture_id,
            "captured_at": payment.captured_at,
            "created_at": payment.created_at,
        }
        for payment in payments
    ]