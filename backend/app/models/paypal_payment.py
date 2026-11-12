from sqlalchemy import (
    Column, Integer, String, ForeignKey, DateTime,
    Numeric, JSON, Boolean, func
)
from sqlalchemy.orm import relationship
from sqlalchemy import Date

from app.core.database import Base


class PayPalPayment(Base):
    __tablename__ = "paypal_payments"

    id = Column(Integer, primary_key=True, index=True)

    milestone_id = Column(
        Integer,
        ForeignKey("milestones.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    client_user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    freelancer_user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )

    paypal_order_id = Column(String(100), unique=True, nullable=True, index=True)
    authorization_id = Column(String(100), unique=True, nullable=True, index=True)
    capture_id = Column(String(100), unique=True, nullable=True, index=True)

    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False)  # Original milestone currency; retained for history.
    paypal_amount = Column(Numeric(12, 2), nullable=True)
    paypal_currency = Column(String(3), nullable=True)
    exchange_rate = Column(Numeric(20, 10), nullable=True)
    exchange_rate_date = Column(Date, nullable=True)
    exchange_rate_source = Column(String(80), nullable=True)
    exchange_rate_fetched_at = Column(DateTime(timezone=True), nullable=True)

    order_status = Column(String(40), default="CREATED", nullable=False)
    authorization_status = Column(String(40), default="PENDING", nullable=False)
    capture_status = Column(String(40), default="NOT_CAPTURED", nullable=False)
    payment_status = Column(String(40), default="PENDING", nullable=False, index=True)

    authorization_expires_at = Column(DateTime(timezone=True), nullable=True)
    authorized_at = Column(DateTime(timezone=True), nullable=True)
    captured_at = Column(DateTime(timezone=True), nullable=True)

    create_request_id = Column(String(100), unique=True, nullable=False)
    authorize_request_id = Column(String(100), unique=True, nullable=False)
    capture_request_id = Column(String(100), unique=True, nullable=False)

    paypal_response = Column(JSON, nullable=True)
    failure_reason = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    milestone = relationship("Milestone")
    project = relationship("Project")