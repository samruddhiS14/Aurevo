from decimal import Decimal

from app.schemas.ai_scope import ProjectScopeData
from app.services.scope_validation import reconcile_scope_data
from app.services.policy_detector import off_platform_reasons


def sample_scope(percentages=("33.33", "33.33", "33.33")):
    milestones = []
    for index, percentage in enumerate(percentages, start=1):
        milestones.append({
            "title": f"Milestone {index}",
            "description": "A sufficiently detailed milestone description.",
            "deliverables": ["A deliverable"],
            "allocation_percentage": percentage,
            "amount": "1.00",
            "review_period_days": 3,
            "completion_criteria": ["Acceptance criteria met"],
        })
    return ProjectScopeData.model_validate({
        "project_objectives": ["Objective"],
        "detailed_scope_of_work": ["Detailed work"],
        "deliverables": ["Deliverable"],
        "milestones": milestones,
        "estimated_duration_days": 30,
        "suggested_budget_allocation": [],
        "acceptance_criteria": ["Acceptance criteria"],
        "revision_limits": "Two revision rounds",
        "client_responsibilities": ["Provide feedback"],
        "freelancer_responsibilities": ["Deliver work"],
        "dependencies_and_assumptions": [],
        "out_of_scope_activities": [],
    })


def test_scope_reconciliation_handles_repeating_percentages_and_rounding():
    result = reconcile_scope_data(sample_scope(), Decimal("12000.00"))
    assert sum(item.amount for item in result.milestones) == Decimal("12000.00")
    assert sum(item.allocation_percentage for item in result.milestones) == Decimal("100.00")
    assert all(item.amount > 0 for item in result.milestones)


def test_scope_reconciliation_rejects_unbalanced_percentage_input():
    import pytest
    from app.services.gemini_errors import GeminiInvalidResponseError
    with pytest.raises(GeminiInvalidResponseError):
        reconcile_scope_data(sample_scope(("20", "20", "20")), Decimal("12000.00"))


def test_off_platform_detector_ignores_benign_mentions():
    benign = [
        "That is a wise approach to the problem.",
        "The signal is noisy in this chart.",
        "We can discuss this on Discord if it is part of the project integration requirements.",
        "The deadline is 12-11-2026.",
        "Please send the report to support@example.com.",
    ]
    assert all(off_platform_reasons(message) == [] for message in benign)


def test_off_platform_detector_flags_explicit_bypass_intent():
    assert "direct_payment_intent" in off_platform_reasons("Please pay directly outside Aurevo.")
    assert "external_channel_intent" in off_platform_reasons("Let's move to WhatsApp to continue the project.")
    assert "external_channel_intent" in off_platform_reasons("Can we switch to Discord for the project chat?")
    assert "direct_payment_intent" in off_platform_reasons("Send a payment through Wise instead of Aurevo.")


def test_usd_quote_is_identity_without_external_request():
    import asyncio
    from app.services.exchange_rate_service import create_paypal_quote
    quote = asyncio.run(create_paypal_quote(Decimal("10.005"), "usd"))
    assert quote.original_currency == "USD"
    assert quote.paypal_currency == "USD"
    assert quote.paypal_amount == Decimal("10.01")
    assert quote.rate == Decimal("1")


def test_legacy_usd_quote_is_safe_identity():
    from types import SimpleNamespace
    from app.services.payment_quote import get_paypal_quote
    payment = SimpleNamespace(amount=Decimal("25.00"), currency="USD", paypal_amount=None, paypal_currency=None)
    assert get_paypal_quote(payment) == (Decimal("25.00"), "USD")


def test_legacy_non_usd_quote_is_blocked_without_snapshot():
    import pytest
    from types import SimpleNamespace
    from app.services.payment_quote import get_paypal_quote, PaymentQuoteError
    payment = SimpleNamespace(amount=Decimal("12000.00"), currency="INR", paypal_amount=None, paypal_currency=None)
    with pytest.raises(PaymentQuoteError):
        get_paypal_quote(payment)


def test_inr_quote_uses_frankfurter_rate_and_cent_rounding(monkeypatch):
    import asyncio
    from types import SimpleNamespace
    from app.services import exchange_rate_service

    class FakeResponse:
        def raise_for_status(self):
            return None
        def json(self):
            return {"rate": 0.01066, "date": "2026-11-11"}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            return False
        async def get(self, url):
            assert url.endswith("/rate/INR/USD")
            return FakeResponse()

    monkeypatch.setattr(exchange_rate_service.httpx, "AsyncClient", FakeClient)
    quote = asyncio.run(exchange_rate_service.create_paypal_quote(Decimal("12000.00"), "INR"))
    assert quote.original_amount == Decimal("12000.00")
    assert quote.paypal_amount == Decimal("127.92")
    assert quote.paypal_currency == "USD"
    assert quote.rate == Decimal("0.01066")
    assert quote.rate_date.isoformat() == "2026-11-11"


def test_application_response_includes_related_project_and_freelancer_fields():
    from datetime import datetime, timezone
    from app.schemas.project import ApplicationResponse

    result = ApplicationResponse.model_validate({
        "id": 1,
        "project_id": 2,
        "freelancer_id": 3,
        "proposal_text": "A proposal with sufficient detail for the client.",
        "proposed_amount": "100.00",
        "estimated_completion_days": 7,
        "relevant_experience": "Relevant experience with similar work.",
        "status": "pending",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "project_title": "Website redesign",
        "currency": "INR",
        "freelancer_name": "Test Freelancer",
    })
    assert result.project_title == "Website redesign"
    assert result.currency == "INR"
    assert result.freelancer_name == "Test Freelancer"
