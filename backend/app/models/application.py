from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    DateTime,
    Numeric,
    func,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Application(Base):
    __tablename__ = "applications"

    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "freelancer_id",
            name="uq_project_freelancer_application",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    freelancer_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    proposal_text = Column(Text, nullable=False)

    proposed_amount = Column(Numeric(12, 2), nullable=True)

    estimated_completion_days = Column(Integer, nullable=True)

    relevant_experience = Column(Text, nullable=True)

    status = Column(
        String(30),
        nullable=False,
        default="pending",
        index=True,
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

    project = relationship("Project", back_populates="applications")

    freelancer = relationship(
        "User",
        foreign_keys=[freelancer_id],
    )

    status_history = relationship(
        "ApplicationStatusHistory",
        back_populates="application",
        cascade="all, delete-orphan",
        order_by="ApplicationStatusHistory.created_at",
    )