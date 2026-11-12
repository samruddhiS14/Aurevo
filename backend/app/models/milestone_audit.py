from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    DateTime,
    JSON,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class MilestoneAudit(Base):
    __tablename__ = "milestone_audit"

    id = Column(Integer, primary_key=True, index=True)

    milestone_id = Column(
        Integer,
        ForeignKey("milestones.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    actor_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    previous_status = Column(String(30), nullable=True)

    new_status = Column(String(30), nullable=False)

    details = Column(JSON, nullable=True)

    description = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    milestone = relationship("Milestone")

    actor = relationship("User")