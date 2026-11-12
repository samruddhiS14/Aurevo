"""Invalidate existing JWTs after password changes.

Revision ID: f6b2d8c41a90
Revises: e71c2a9b4f10
"""
from alembic import op
import sqlalchemy as sa

revision = "f6b2d8c41a90"
down_revision = "e71c2a9b4f10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("users", "token_version")
