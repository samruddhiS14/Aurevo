
from sqlalchemy import (
    Column, Integer, String, ForeignKey,
    DateTime, Numeric, func
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    milestone_id = Column(
        Integer,
        ForeignKey("milestones.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    client_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    freelancer_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")

    status = Column(
        String(30),
        nullable=False,
        default="created",
        index=True,
    )

    paypal_order_id = Column(String(150), unique=True, nullable=True)
    paypal_authorization_id = Column(String(150), nullable=True)
    paypal_capture_id = Column(String(150), nullable=True)

    authorization_expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    authorized_at = Column(DateTime(timezone=True), nullable=True)
    captured_at = Column(DateTime(timezone=True), nullable=True)

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

    project = relationship("Project", back_populates="payments")
    milestone = relationship("Milestone", back_populates="payments")

    client = relationship("User", foreign_keys=[client_id])
    freelancer = relationship("User", foreign_keys=[freelancer_id])
