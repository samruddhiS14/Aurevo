from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, UniqueConstraint, CheckConstraint, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class ProjectReview(Base):
    __tablename__ = "project_reviews"
    __table_args__ = (
        UniqueConstraint("project_id", "reviewer_id", name="uq_project_review_reviewer"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_project_review_rating"),
    )
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewee_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    reviewee = relationship("User", foreign_keys=[reviewee_id])
