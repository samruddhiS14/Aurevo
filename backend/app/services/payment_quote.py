
"""Safe access to the immutable PayPal currency quote stored on a payment."""

from decimal import Decimal, InvalidOperation


class PaymentQuoteError(Exception):
    """The PayPal amount/currency cannot be established safely from stored data."""


def get_paypal_quote(payment) -> tuple[Decimal, str]:

    amount = payment.paypal_amount
    currency = payment.paypal_currency

    # Use the saved PayPal quote when available.
    if amount is not None and currency:

        normalized_currency = str(currency).upper().strip()

        if (
            not normalized_currency.isalpha()
            or len(normalized_currency) != 3
        ):
            raise PaymentQuoteError(
                "Stored PayPal currency is invalid."
            )

        try:
            normalized_amount = Decimal(str(amount))

        except (InvalidOperation, ValueError, TypeError) as exc:
            raise PaymentQuoteError(
                "Stored PayPal amount is invalid."
            ) from exc

        if not normalized_amount.is_finite() or normalized_amount <= 0:
            raise PaymentQuoteError(
                "Stored PayPal amount must be positive."
            )

        return normalized_amount, normalized_currency

    # Legacy USD payments can safely use their original amount.
    if (
        amount is None
        and not currency
        and str(payment.currency).upper() == "USD"
    ):
        return Decimal(str(payment.amount)), "USD"

    # Do not guess the amount for incomplete legacy payments.
    raise PaymentQuoteError(
        "This legacy payment has no complete saved PayPal currency quote. "
        "Do not authorize or capture it until it has been reconciled."
    )
