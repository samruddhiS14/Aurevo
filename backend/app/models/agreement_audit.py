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


class AgreementAudit(Base):
    __tablename__ = "agreement_audit"

    id = Column(Integer, primary_key=True, index=True)

    agreement_id = Column(
        Integer,
        ForeignKey("agreements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    version_id = Column(
        Integer,
        ForeignKey("agreement_versions.id", ondelete="CASCADE"),
        nullable=True,
    )

    actor_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    action = Column(String(50), nullable=False)

    details = Column(JSON, nullable=True)

    description = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    actor = relationship("User")

    version = relationship("AgreementVersion")