from datetime import date, datetime
from decimal import Decimal
from typing import Literal
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


ExperienceLevel = Literal["entry", "intermediate", "expert"]
ProjectType = Literal["fixed_price", "hourly"]
MilestoneStructure = Literal[
    "milestone_based",
    "single_payment",
    "custom",
]


class ProjectCreate(BaseModel):
    title: str = Field(min_length=5, max_length=200)
    description: str = Field(min_length=30)
    required_skills: list[str] = Field(min_length=1)
    category: str = Field(min_length=2, max_length=100)
    budget: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    start_date: date | None = None
    due_date: datetime | None = None
    expected_deliverables: list[str] = Field(min_length=1)
    experience_level: ExperienceLevel
    project_type: ProjectType
    preferred_milestone_structure: MilestoneStructure = "milestone_based"

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, value):
        normalized = value.strip().upper()
        if not re.fullmatch(r"[A-Z]{3}", normalized):
            raise ValueError("Currency must be a three-letter code such as INR or USD.")
        return normalized

    @field_validator("required_skills", "expected_deliverables")
    @classmethod
    def clean_list(cls, values):
        cleaned = [item.strip() for item in values if item.strip()]
        if not cleaned:
            raise ValueError("At least one item is required.")
        return cleaned


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    freelancer_id: int | None
    title: str
    description: str
    required_skills: list[str] | None
    category: str | None
    budget: Decimal | None
    currency: str
    status: str
    start_date: date | None
    due_date: datetime | None
    expected_deliverables: list[str] | None
    experience_level: str | None
    project_type: str | None
    preferred_milestone_structure: str | None
    created_at: datetime


class ApplicationCreate(BaseModel):
    proposal_text: str = Field(min_length=30)
    proposed_amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    estimated_completion_days: int = Field(gt=0, le=3650)
    relevant_experience: str = Field(min_length=20)


class ApplicationStatusUpdate(BaseModel):
    status: Literal["shortlisted", "rejected"]


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    freelancer_id: int
    proposal_text: str
    proposed_amount: Decimal | None
    estimated_completion_days: int | None
    relevant_experience: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    project_title: str | None = None
    currency: str | None = None
    freelancer_name: str | None = None
    freelancer_email: str | None = None
    freelancer_country: str | None = None
    freelancer_title: str | None = None
    freelancer_skills: str | None = None
    freelancer_experience_years: int | None = None