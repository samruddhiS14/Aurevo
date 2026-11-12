from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    DateTime,
    Boolean,
    JSON,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class AIScopeVersion(Base):
    __tablename__ = "ai_scope_versions"

    id = Column(Integer, primary_key=True, index=True)

    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    version_number = Column(Integer, nullable=False)

    scope_data = Column(JSON, nullable=False)

    status = Column(
        String(30),
        nullable=False,
        default="draft",
        index=True,
    )

    generated_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    approved_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    is_approved = Column(Boolean, nullable=False, default=False)

    approved_at = Column(DateTime(timezone=True), nullable=True)

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

    project = relationship("Project")

    generator = relationship("User", foreign_keys=[generated_by])

    approver = relationship("User", foreign_keys=[approved_by])