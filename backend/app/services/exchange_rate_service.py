
"""Frankfurter-backed, immutable USD quote snapshots for PayPal payments."""

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

import httpx


FRANKFURTER_BASE_URL = "https://api.frankfurter.dev/v2"
PAYPAL_CURRENCY = "USD"
CENT = Decimal("0.01")


class ExchangeRateError(Exception):
    """A quote could not be obtained or validated."""


@dataclass(frozen=True)
class ExchangeQuote:
    original_amount: Decimal
    original_currency: str
    paypal_amount: Decimal
    paypal_currency: str
    rate: Decimal
    rate_date: date
    source: str
    fetched_at: datetime


async def create_paypal_quote(
    amount: Decimal,
    currency: str,
) -> ExchangeQuote:

    # Validate and normalize the original amount.
    try:
        original_amount = Decimal(str(amount)).quantize(
            CENT,
            rounding=ROUND_HALF_UP,
        )
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ExchangeRateError(
            "Invalid milestone payment amount."
        ) from exc

    # Validate the original currency.
    original_currency = str(currency).upper().strip()

    if not original_currency.isalpha() or len(original_currency) != 3:
        raise ExchangeRateError(
            "Project currency must be a valid three-letter currency code."
        )

    if not original_amount.is_finite() or original_amount <= 0:
        raise ExchangeRateError(
            "Payment amount must be positive."
        )

    fetched_at = datetime.now(timezone.utc)

    # USD does not require conversion.
    if original_currency == PAYPAL_CURRENCY:
        rate = Decimal("1")
        rate_date = fetched_at.date()

    else:
        # Fetch exchange rate from Frankfurter.
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(8.0, connect=3.0)
            ) as client:

                response = await client.get(
                    f"{FRANKFURTER_BASE_URL}/rate/"
                    f"{original_currency}/{PAYPAL_CURRENCY}"
                )

                response.raise_for_status()
                data = response.json()

            fetched_at = datetime.now(timezone.utc)

            rate = Decimal(str(data["rate"]))
            rate_date = date.fromisoformat(data["date"])

            if not rate.is_finite() or rate <= 0:
                raise ValueError("Invalid exchange rate.")

        except (
            httpx.HTTPError,
            ValueError,
            KeyError,
            TypeError,
            InvalidOperation,
        ) as exc:

            raise ExchangeRateError(
                "A reliable exchange-rate quote is unavailable. "
                "Please retry later."
            ) from exc

    # Convert original amount into USD.
    converted = (original_amount * rate).quantize(
        CENT,
        rounding=ROUND_HALF_UP,
    )

    if not converted.is_finite() or converted <= 0:
        raise ExchangeRateError(
            "Converted PayPal amount is below the supported precision."
        )

    return ExchangeQuote(
        original_amount=original_amount,
        original_currency=original_currency,
        paypal_amount=converted,
        paypal_currency=PAYPAL_CURRENCY,
        rate=rate,
        rate_date=rate_date,
        source=(
            "Frankfurter v2"
            if original_currency != PAYPAL_CURRENCY
            else "identity"
        ),
        fetched_at=fetched_at,
    )
