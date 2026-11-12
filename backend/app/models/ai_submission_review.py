from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    JSON,
    DateTime,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class AISubmissionReview(Base):
    __tablename__ = "ai_submission_reviews"

    id = Column(Integer, primary_key=True, index=True)

    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    milestone_id = Column(
        Integer,
        ForeignKey("milestones.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    scope_version_id = Column(
        Integer,
        ForeignKey("ai_scope_versions.id", ondelete="RESTRICT"),
        nullable=False,
    )

    submitted_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    submission_description = Column(Text, nullable=False)

    review_result = Column(JSON, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    project = relationship("Project")

    milestone = relationship("Milestone")

    scope_version = relationship("AIScopeVersion")

    submitter = relationship("User")