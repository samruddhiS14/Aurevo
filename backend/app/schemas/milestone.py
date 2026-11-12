from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


MilestoneStatus = Literal[
    "not_started",
    "in_progress",
    "submitted",
    "under_review",
    "revision_requested",
    "approved",
    "payment_pending",
    "paid",
    "disputed",
]


class MilestoneProgressUpdate(BaseModel):
    progress_percentage: int = Field(ge=0, le=100)


class MilestoneSubmissionRequest(BaseModel):
    submission_url: str = Field(min_length=5, max_length=2000)
    submission_notes: str = Field(min_length=10, max_length=5000)


class MilestoneReviewRequest(BaseModel):
    action: Literal["approve", "request_revision"]
    explanation: str | None = Field(default=None, max_length=5000)


class MilestoneDisputeRequest(BaseModel):
    explanation: str = Field(min_length=20, max_length=5000)


class MilestoneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    agreement_version_id: int | None
    is_current: bool

    id: int
    project_id: int
    title: str
    description: str
    amount: Decimal
    currency: str
    due_date: datetime | None
    status: str
    progress_percentage: int
    deliverables: list | None
    completion_criteria: list | None
    review_period_days: int
    submission_url: str | None
    submission_notes: str | None
    submitted_at: datetime | None
    review_deadline: datetime | None
    revision_explanation: str | None
    approved_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime