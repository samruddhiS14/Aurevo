"""Add ADMIN to the existing user_role enum.

Revision ID: d4a9c81e7b20
Revises: c91a4d72f103
"""
from alembic import op

revision = "d4a9c81e7b20"
down_revision = "c91a4d72f103"
branch_labels = None
depends_on = None

def upgrade() -> None:
    # PostgreSQL enum values are intentionally retained on downgrade to avoid
    # invalidating any administrator rows created after this migration.
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'ADMIN'")

def downgrade() -> None:
    pass
