from sqlalchemy import Column, Integer, String, DateTime, JSON, func
from app.core.database import Base


class PayPalWebhookEvent(Base):
    __tablename__ = "paypal_webhook_events"

    id = Column(Integer, primary_key=True, index=True)

    event_id = Column(String(120), unique=True, nullable=False, index=True)
    event_type = Column(String(120), nullable=False, index=True)

    resource_id = Column(String(120), nullable=True, index=True)
    payload = Column(JSON, nullable=False)

    processed = Column(String(40), default="RECEIVED", nullable=False)
    processing_error = Column(String(1000), nullable=True)

    received_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    