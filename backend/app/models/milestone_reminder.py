from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint, func
from app.core.database import Base

class MilestoneReminder(Base):
    __tablename__ = "milestone_reminders"
    __table_args__ = (UniqueConstraint("milestone_id", "submission_at", "reminder_offset_minutes", name="uq_milestone_reminder_submission_offset"),)
    id = Column(Integer, primary_key=True, index=True)
    milestone_id = Column(Integer, ForeignKey("milestones.id", ondelete="CASCADE"), nullable=False, index=True)
    submission_at = Column(DateTime(timezone=True), nullable=False)
    reminder_offset_minutes = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
