
from pydantic import BaseModel
from typing import Any
from decimal import Decimal


class DashboardStats(BaseModel):
    total_projects: int = 0
    active_projects: int = 0
    completed_projects: int = 0
    pending_applications: int = 0
    total_authorized: Decimal = Decimal("0.00")
    total_captured: Decimal = Decimal("0.00")
    pending_milestone_payments: int = 0
    awaiting_submission: int = 0
    awaiting_approval: int = 0


class DashboardResponse(BaseModel):
    role: str
    stats: dict[str, Any]
    recent_transactions: list[dict[str, Any]]
    recent_activity: list[dict[str, Any]]
    upcoming_deadlines: list[dict[str, Any]]
    notifications: list[dict[str, Any]]
