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
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Agreement(Base):
    __tablename__ = "agreements"

    id = Column(Integer, primary_key=True, index=True)

    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    active_version_id = Column(
        Integer,
        ForeignKey("agreement_versions.id", ondelete="SET NULL", use_alter=True, name="fk_agreements_active_version"),
        nullable=True,
    )

    status = Column(
        String(30),
        nullable=False,
        default="pending",
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

    project = relationship(
        "Project",
        foreign_keys=[project_id],
    )

    versions = relationship(
        "AgreementVersion",
        back_populates="agreement",
        foreign_keys="AgreementVersion.agreement_id",
        cascade="all, delete-orphan",
        order_by="AgreementVersion.version_number",
    )


class AgreementVersion(Base):
    __tablename__ = "agreement_versions"

    __table_args__ = (
        UniqueConstraint(
            "agreement_id",
            "version_number",
            name="uq_agreement_version_number",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    agreement_id = Column(
        Integer,
        ForeignKey("agreements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    version_number = Column(Integer, nullable=False)

    previous_version_id = Column(
        Integer,
        ForeignKey("agreement_versions.id", ondelete="SET NULL", use_alter=True, name="fk_agreements_active_version"),
        nullable=True,
    )

    # Complete agreement snapshot.
    agreement_data = Column(JSON, nullable=False)

    # Fields changed compared with the previous version.
    changed_fields = Column(JSON, nullable=True)

    change_summary = Column(Text, nullable=True)

    created_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    client_approved = Column(Boolean, nullable=False, default=False)

    freelancer_approved = Column(Boolean, nullable=False, default=False)

    client_approved_at = Column(DateTime(timezone=True), nullable=True)

    freelancer_approved_at = Column(DateTime(timezone=True), nullable=True)

    status = Column(
        String(30),
        nullable=False,
        default="pending_approval",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    agreement = relationship(
        "Agreement",
        back_populates="versions",
        foreign_keys=[agreement_id],
    )

    previous_version = relationship(
        "AgreementVersion",
        remote_side="AgreementVersion.id",
        foreign_keys=[previous_version_id],
    )

    creator = relationship(
        "User",
        foreign_keys=[created_by],
    )