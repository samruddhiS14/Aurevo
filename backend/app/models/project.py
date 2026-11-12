from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey,
    DateTime, Date, Numeric, JSON, func, Index
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Project(Base):
    __tablename__ = "projects"

    __table_args__ = (
        Index("ix_projects_status_created", "status", "created_at"),
        Index("ix_projects_category_status", "category", "status"),
    )

    id = Column(Integer, primary_key=True, index=True)

    client_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    freelancer_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)

    required_skills = Column(JSON, nullable=True, default=list)
    category = Column(String(100), nullable=True)

    budget = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(3), nullable=False, default="USD")

    status = Column(String(30), nullable=False, default="open", index=True)

    start_date = Column(Date, nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)

    expected_deliverables = Column(JSON, nullable=True, default=list)
    experience_level = Column(String(30), nullable=True)
    project_type = Column(String(30), nullable=True)

    preferred_milestone_structure = Column(
        String(50),
        nullable=True,
        default="milestone_based",
    )

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

    client = relationship("User", foreign_keys=[client_id])
    freelancer = relationship("User", foreign_keys=[freelancer_id])

    applications = relationship(
        "Application",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    milestones = relationship(
        "Milestone",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    payments = relationship("Payment", back_populates="project")

    activities = relationship(
        "Activity",
        back_populates="project",
        cascade="all, delete-orphan",
    )