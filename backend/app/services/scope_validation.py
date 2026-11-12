
"""Deterministic validation and budget reconciliation for project scopes."""

from decimal import Decimal, ROUND_HALF_UP

from app.schemas.ai_scope import ProjectScopeData

CENT = Decimal("0.01")


def reconcile_scope_data(
    scope: ProjectScopeData,
    project_budget: Decimal,
) -> ProjectScopeData:
    """Ensure milestone percentages and amounts match the project budget."""

    budget = Decimal(str(project_budget)).quantize(
        CENT,
        rounding=ROUND_HALF_UP,
    )

    if not budget.is_finite() or budget <= 0:
        raise ValueError("A positive project budget is required.")

    if not scope.milestones:
        raise ValueError("At least one milestone is required.")

    raw_total = sum(
        (item.allocation_percentage for item in scope.milestones),
        Decimal("0"),
    )

    if raw_total <= 0:
        raise ValueError("Milestone allocation percentages must be positive.")

    milestones = []
    assigned_percentage = Decimal("0")
    assigned_amount = Decimal("0")

    for index, item in enumerate(scope.milestones):
        is_last = index == len(scope.milestones) - 1

        if is_last:
            percentage = Decimal("100.00") - assigned_percentage
            amount = budget - assigned_amount
        else:
            percentage = (
                item.allocation_percentage / raw_total * Decimal("100")
            ).quantize(CENT, rounding=ROUND_HALF_UP)

            amount = (
                budget * percentage / Decimal("100")
            ).quantize(CENT, rounding=ROUND_HALF_UP)

            assigned_percentage += percentage
            assigned_amount += amount

        if percentage <= 0 or amount <= 0:
            raise ValueError(
                "The project budget is too small for the milestone allocation."
            )

        milestones.append(
            item.model_copy(
                update={
                    "allocation_percentage": percentage,
                    "amount": amount,
                }
            )
        )

    allocations = [
        {
            "milestone": item.title,
            "percentage": str(item.allocation_percentage),
            "amount": str(item.amount),
        }
        for item in milestones
    ]

    return scope.model_copy(
        update={
            "milestones": milestones,
            "suggested_budget_allocation": allocations,
        }
    )
