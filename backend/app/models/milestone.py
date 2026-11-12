from sqlalchemy import Boolean
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    DateTime,
    Numeric,
    JSON,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Milestone(Base):
    __tablename__ = "milestones"

    id = Column(Integer, primary_key=True, index=True)

    agreement_version_id = Column(Integer, ForeignKey("agreement_versions.id", ondelete="SET NULL"), nullable=True, index=True)
    is_current = Column(Boolean, nullable=False, default=True, index=True)

    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title = Column(String(200), nullable=False)

    description = Column(Text, nullable=False)

    amount = Column(Numeric(12, 2), nullable=False)

    currency = Column(String(3), nullable=False, default="USD")

    due_date = Column(DateTime(timezone=True), nullable=True)

    status = Column(
        String(30),
        nullable=False,
        default="not_started",
        index=True,
    )

    progress_percentage = Column(
        Integer,
        nullable=False,
        default=0,
    )

    deliverables = Column(JSON, nullable=True)

    completion_criteria = Column(JSON, nullable=True)

    review_period_days = Column(
        Integer,
        nullable=False,
        default=3,
    )

    submission_url = Column(Text, nullable=True)

    submission_notes = Column(Text, nullable=True)

    submitted_at = Column(DateTime(timezone=True), nullable=True)

    review_deadline = Column(DateTime(timezone=True), nullable=True)

    revision_explanation = Column(Text, nullable=True)

    approved_at = Column(DateTime(timezone=True), nullable=True)

    completed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    project = relationship(
        "Project",
        back_populates="milestones",
    )

    payments = relationship(
        "Payment",
        back_populates="milestone",
    )