
import base64
from decimal import Decimal, InvalidOperation

import httpx

from app.core.config import settings


class PayPalError(Exception):
    """Raised when a PayPal operation fails."""


class PayPalService:

    def __init__(self):
        if not settings.PAYPAL_CLIENT_ID or not settings.PAYPAL_CLIENT_SECRET:
            raise PayPalError(
                "PayPal credentials are not configured."
            )

        self.base_url = settings.PAYPAL_BASE_URL.rstrip("/")
        self.client_id = settings.PAYPAL_CLIENT_ID
        self.client_secret = settings.PAYPAL_CLIENT_SECRET

    @staticmethod
    def _get_error_message(response):
        """Extract a useful, safe error message from PayPal's response."""

        try:
            data = response.json()
        except ValueError:
            return f"PayPal returned HTTP {response.status_code}."

        if not isinstance(data, dict):
            return f"PayPal returned HTTP {response.status_code}."

        name = data.get("name", "PayPal API Error")
        message = data.get("message", "No error message provided.")

        details = data.get("details", [])
        detail_messages = []

        if isinstance(details, list):
            for detail in details:
                if isinstance(detail, dict):
                    issue = detail.get("issue")
                    description = detail.get("description")

                    if issue and description:
                        detail_messages.append(
                            f"{issue}: {description}"
                        )
                    elif issue:
                        detail_messages.append(str(issue))
                    elif description:
                        detail_messages.append(str(description))

        debug_id = data.get("debug_id")

        error = (
            f"PayPal error ({response.status_code}): "
            f"{name} - {message}"
        )

        if detail_messages:
            error += " Details: " + "; ".join(detail_messages)

        if debug_id:
            error += f" Debug ID: {debug_id}"

        return error

    async def get_access_token(self):
        """Authenticate with PayPal and obtain an access token."""

        credentials = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(
            credentials.encode()
        ).decode()

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.base_url}/v1/oauth2/token",
                    headers={
                        "Authorization": f"Basic {encoded}",
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                    data={
                        "grant_type": "client_credentials"
                    },
                )

        except httpx.RequestError as exc:
            raise PayPalError(
                "Could not connect to PayPal authentication service."
            ) from exc

        if response.status_code != 200:
            raise PayPalError(
                self._get_error_message(response)
            )

        try:
            data = response.json()
            access_token = data["access_token"]
        except (ValueError, KeyError, TypeError) as exc:
            raise PayPalError(
                "PayPal authentication returned an invalid response."
            ) from exc

        return access_token

    async def request(
        self,
        method,
        endpoint,
        payload=None,
        request_id=None,
    ):
        """Send an authenticated request to the PayPal API."""

        token = await self.get_access_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

        if request_id:
            headers["PayPal-Request-Id"] = request_id

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.request(
                    method,
                    f"{self.base_url}{endpoint}",
                    headers=headers,
                    json=payload,
                )

        except httpx.RequestError as exc:
            raise PayPalError(
                f"Could not connect to PayPal API while calling {endpoint}."
            ) from exc

        if response.status_code not in (200, 201):
            raise PayPalError(
                self._get_error_message(response)
            )

        if not response.content:
            return {}

        try:
            return response.json()
        except ValueError as exc:
            raise PayPalError(
                "PayPal returned an invalid JSON response."
            ) from exc

    async def create_order(
        self,
        milestone,
        payment_id,
        request_id,
        amount=None,
        currency=None,
    ):
        """Create a PayPal authorization order."""

        try:
            order_amount = Decimal(
                str(
                    amount
                    if amount is not None
                    else milestone.amount
                )
            )
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise PayPalError(
                "Invalid payment amount supplied to PayPal."
            ) from exc

        if not order_amount.is_finite() or order_amount <= 0:
            raise PayPalError(
                "PayPal order amount must be positive."
            )

        order_currency = str(
            currency or milestone.currency
        ).upper().strip()

        if not order_currency.isalpha() or len(order_currency) != 3:
            raise PayPalError(
                "Invalid PayPal currency code."
            )

        payload = {
            "intent": "AUTHORIZE",
            "purchase_units": [
                {
                    "reference_id": f"milestone-{milestone.id}",
                    "custom_id": str(payment_id),
                    "description": f"Aurevo milestone {milestone.id}",
                    "amount": {
                        "currency_code": order_currency,
                        "value": f"{order_amount:.2f}",
                    },
                }
            ],
            "payment_source": {
                "paypal": {
                    "experience_context": {
                        "brand_name": "Aurevo",
                        "user_action": "PAY_NOW",
                        "return_url": settings.PAYPAL_RETURN_URL,
                        "cancel_url": settings.PAYPAL_CANCEL_URL,
                    }
                }
            },
        }

        return await self.request(
            "POST",
            "/v2/checkout/orders",
            payload,
            request_id,
        )

    async def get_order(self, order_id):
        """Retrieve a PayPal order."""

        return await self.request(
            "GET",
            f"/v2/checkout/orders/{order_id}",
        )

    async def authorize_order(self, order_id, request_id):
        """Authorize an approved PayPal order."""

        return await self.request(
            "POST",
            f"/v2/checkout/orders/{order_id}/authorize",
            {},
            request_id,
        )

    async def capture_authorization(
        self,
        authorization_id,
        amount,
        currency,
        request_id,
    ):
        """Capture funds from an existing authorization."""

        try:
            capture_amount = Decimal(str(amount))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise PayPalError(
                "Invalid capture amount."
            ) from exc

        if not capture_amount.is_finite() or capture_amount <= 0:
            raise PayPalError(
                "Capture amount must be positive."
            )

        capture_currency = str(currency).upper().strip()

        if not capture_currency.isalpha() or len(capture_currency) != 3:
            raise PayPalError(
                "Invalid capture currency."
            )

        payload = {
            "amount": {
                "value": f"{capture_amount:.2f}",
                "currency_code": capture_currency,
            },
            "final_capture": True,
        }

        return await self.request(
            "POST",
            f"/v2/payments/authorizations/{authorization_id}/capture",
            payload,
            request_id,
        )

    async def verify_webhook(self, headers, event):
        """Verify a PayPal webhook signature."""

        if not settings.PAYPAL_WEBHOOK_ID:
            raise PayPalError(
                "PayPal webhook ID is not configured."
            )

        payload = {
            "auth_algo": headers.get("paypal-auth-algo"),
            "cert_url": headers.get("paypal-cert-url"),
            "transmission_id": headers.get("paypal-transmission-id"),
            "transmission_sig": headers.get("paypal-transmission-sig"),
            "transmission_time": headers.get("paypal-transmission-time"),
            "webhook_id": settings.PAYPAL_WEBHOOK_ID,
            "webhook_event": event,
        }

        result = await self.request(
            "POST",
            "/v1/notifications/verify-webhook-signature",
            payload,
        )

        return result.get("verification_status") == "SUCCESS"
