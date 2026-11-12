from datetime import datetime
from decimal import Decimal
from typing import Literal
import re
from pydantic import field_validator

from pydantic import BaseModel, ConfigDict, Field


class AgreementMilestone(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = Field(min_length=3, max_length=3)
    due_date: datetime | None = None
    deliverables: list[str] = Field(min_length=1)
    completion_criteria: list[str] = Field(min_length=1)
    review_period_days: int = Field(ge=1, le=30)

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value):
        normalized = value.strip().upper()
        if not re.fullmatch(r"[A-Z]{3}", normalized):
            raise ValueError("Currency must be a three-letter code.")
        return normalized


class AgreementData(BaseModel):
    client_details: dict
    freelancer_details: dict

    project_title: str
    project_description: str

    deliverables: list[str] = Field(min_length=1)

    milestones: list[AgreementMilestone] = Field(min_length=1)

    total_budget: Decimal = Field(gt=0, max_digits=12, decimal_places=2)

    currency: str = Field(min_length=3, max_length=3)

    estimated_duration_days: int = Field(gt=0)

    revision_limits: str

    acceptance_criteria: list[str] = Field(min_length=1)

    client_responsibilities: list[str]

    freelancer_responsibilities: list[str]

    cancellation_terms: str

    dispute_procedure: str

    payment_conditions: str

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value):
        normalized = value.strip().upper()
        if not re.fullmatch(r"[A-Z]{3}", normalized):
            raise ValueError("Currency must be a three-letter code.")
        return normalized


class AgreementGenerateRequest(BaseModel):
    change_summary: str | None = None


class AgreementVersionCreate(BaseModel):
    agreement_data: AgreementData
    change_summary: str = Field(min_length=5, max_length=2000)


class AgreementApprovalRequest(BaseModel):
    confirm: Literal[True]


class AgreementVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    agreement_id: int
    version_number: int
    previous_version_id: int | None
    agreement_data: dict
    changed_fields: list | None
    change_summary: str | None
    client_approved: bool
    freelancer_approved: bool
    status: str
    created_at: datetime


class AgreementAuditResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    agreement_id: int
    version_id: int | None
    actor_user_id: int | None
    action: str
    details: dict | None
    description: str | None
    created_at: datetime