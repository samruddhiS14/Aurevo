from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MilestoneRecommendation(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10)
    deliverables: list[str] = Field(min_length=1)
    allocation_percentage: Decimal = Field(gt=0, le=100)
    amount: Decimal = Field(gt=0, decimal_places=2, max_digits=12)
    suggested_submission_date: datetime | None = None
    review_period_days: int = Field(ge=1, le=30)
    completion_criteria: list[str] = Field(min_length=1)


class ProjectScopeData(BaseModel):
    project_objectives: list[str] = Field(min_length=1)
    detailed_scope_of_work: list[str] = Field(min_length=1)
    deliverables: list[str] = Field(min_length=1)

    milestones: list[MilestoneRecommendation] = Field(min_length=1)

    estimated_duration_days: int = Field(gt=0, le=3650)

    suggested_budget_allocation: list[dict]

    acceptance_criteria: list[str] = Field(min_length=1)

    revision_limits: str = Field(min_length=5)

    client_responsibilities: list[str] = Field(min_length=1)

    freelancer_responsibilities: list[str] = Field(min_length=1)

    dependencies_and_assumptions: list[str]

    out_of_scope_activities: list[str]


class ScopeGenerationRequest(BaseModel):
    additional_instructions: str | None = None


class ScopeEditRequest(BaseModel):
    scope_data: ProjectScopeData


class ScopeVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    version_number: int
    scope_data: dict
    status: str
    is_approved: bool
    generated_by: int | None
    approved_by: int | None
    approved_at: datetime | None
    created_at: datetime


class CopilotRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)


class SubmissionComparisonRequest(BaseModel):
    submission_description: str = Field(min_length=20, max_length=10000)


class SubmissionComparisonResult(BaseModel):
    requirements_fulfilled: list[str]
    potentially_missing_requirements: list[str]
    possible_scope_deviations: list[str]
    clarification_questions: list[str]
    overall_assessment: Literal[
        "appears_aligned",
        "partially_aligned",
        "needs_clarification",
    ]
    disclaimer: str