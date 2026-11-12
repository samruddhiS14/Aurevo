"""Add immutable currency quote snapshot to PayPal payments.

Revision ID: e71c2a9b4f10
Revises: d4a9c81e7b20
"""
from alembic import op
import sqlalchemy as sa

revision = "e71c2a9b4f10"
down_revision = "d4a9c81e7b20"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("paypal_payments", sa.Column("paypal_amount", sa.Numeric(12, 2), nullable=True))
    op.add_column("paypal_payments", sa.Column("paypal_currency", sa.String(3), nullable=True))
    op.add_column("paypal_payments", sa.Column("exchange_rate", sa.Numeric(20, 10), nullable=True))
    op.add_column("paypal_payments", sa.Column("exchange_rate_date", sa.Date(), nullable=True))
    op.add_column("paypal_payments", sa.Column("exchange_rate_source", sa.String(80), nullable=True))
    op.add_column("paypal_payments", sa.Column("exchange_rate_fetched_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("paypal_payments", "exchange_rate_fetched_at")
    op.drop_column("paypal_payments", "exchange_rate_source")
    op.drop_column("paypal_payments", "exchange_rate_date")
    op.drop_column("paypal_payments", "exchange_rate")
    op.drop_column("paypal_payments", "paypal_currency")
    op.drop_column("paypal_payments", "paypal_amount")
