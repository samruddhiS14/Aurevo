"""complete existing agreement, payment, workspace and account schema

Revision ID: c91a4d72f103
Revises: b2e1ff42ff04
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "c91a4d72f103"
down_revision: Union[str, Sequence[str], None] = "b2e1ff42ff04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Agreement/version tables were present in the ORM but absent from the migration chain.
    op.create_table(
        "agreements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("active_version_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_agreements_id", "agreements", ["id"])
    op.create_index("ix_agreements_project_id", "agreements", ["project_id"], unique=True)
    op.create_table(
        "agreement_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("agreement_id", sa.Integer(), sa.ForeignKey("agreements.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("previous_version_id", sa.Integer(), sa.ForeignKey("agreement_versions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("agreement_data", sa.JSON(), nullable=False),
        sa.Column("changed_fields", sa.JSON(), nullable=True),
        sa.Column("change_summary", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("client_approved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("freelancer_approved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("client_approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("freelancer_approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending_approval"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("agreement_id", "version_number", name="uq_agreement_version_number"),
    )
    op.create_index("ix_agreement_versions_id", "agreement_versions", ["id"])
    op.create_index("ix_agreement_versions_agreement_id", "agreement_versions", ["agreement_id"])
    with op.batch_alter_table("agreements") as batch_op:
        batch_op.create_foreign_key("fk_agreements_active_version", "agreement_versions", ["active_version_id"], ["id"], ondelete="SET NULL")

    # Extend the Phase 5 milestone table to match the Phase 6+ ORM model.
    op.execute("UPDATE milestones SET description = '' WHERE description IS NULL")
    op.add_column("milestones", sa.Column("agreement_version_id", sa.Integer(), nullable=True))
    op.add_column("milestones", sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("milestones", sa.Column("progress_percentage", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("milestones", sa.Column("deliverables", sa.JSON(), nullable=True))
    op.add_column("milestones", sa.Column("completion_criteria", sa.JSON(), nullable=True))
    op.add_column("milestones", sa.Column("review_period_days", sa.Integer(), nullable=False, server_default="3"))
    op.add_column("milestones", sa.Column("review_deadline", sa.DateTime(timezone=True), nullable=True))
    op.add_column("milestones", sa.Column("revision_explanation", sa.Text(), nullable=True))
    op.add_column("milestones", sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("milestones", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    with op.batch_alter_table("milestones") as batch_op:
        batch_op.alter_column("description", existing_type=sa.Text(), nullable=False)
        batch_op.alter_column("submission_url", existing_type=sa.String(1000), type_=sa.Text(), existing_nullable=True)
    with op.batch_alter_table("milestones") as batch_op:
        batch_op.create_foreign_key("fk_milestones_agreement_version", "agreement_versions", ["agreement_version_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_milestones_agreement_version_id", "milestones", ["agreement_version_id"])
    op.create_index("ix_milestones_is_current", "milestones", ["is_current"])

    op.create_table(
        "agreement_audit",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("agreement_id", sa.Integer(), sa.ForeignKey("agreements.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_id", sa.Integer(), sa.ForeignKey("agreement_versions.id", ondelete="CASCADE"), nullable=True),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(50), nullable=False), sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_agreement_audit_id", "agreement_audit", ["id"])
    op.create_index("ix_agreement_audit_agreement_id", "agreement_audit", ["agreement_id"])

    op.create_table(
        "milestone_audit",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("milestone_id", sa.Integer(), sa.ForeignKey("milestones.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("previous_status", sa.String(30), nullable=True), sa.Column("new_status", sa.String(30), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True), sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_milestone_audit_id", "milestone_audit", ["id"])
    op.create_index("ix_milestone_audit_milestone_id", "milestone_audit", ["milestone_id"])

    op.create_table(
        "ai_scope_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False), sa.Column("scope_data", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("generated_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("approved_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_approved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_ai_scope_versions_id", "ai_scope_versions", ["id"])
    op.create_index("ix_ai_scope_versions_project_id", "ai_scope_versions", ["project_id"])
    op.create_index("ix_ai_scope_versions_status", "ai_scope_versions", ["status"])

    op.create_table(
        "ai_submission_reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("milestone_id", sa.Integer(), sa.ForeignKey("milestones.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scope_version_id", sa.Integer(), sa.ForeignKey("ai_scope_versions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("submitted_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("submission_description", sa.Text(), nullable=False), sa.Column("review_result", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_ai_submission_reviews_id", "ai_submission_reviews", ["id"])
    op.create_index("ix_ai_submission_reviews_project_id", "ai_submission_reviews", ["project_id"])
    op.create_index("ix_ai_submission_reviews_milestone_id", "ai_submission_reviews", ["milestone_id"])

    op.create_table(
        "paypal_payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("milestone_id", sa.Integer(), sa.ForeignKey("milestones.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("client_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("freelancer_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("paypal_order_id", sa.String(100), nullable=True),
        sa.Column("authorization_id", sa.String(100), nullable=True),
        sa.Column("capture_id", sa.String(100), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False), sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("order_status", sa.String(40), nullable=False, server_default="CREATED"),
        sa.Column("authorization_status", sa.String(40), nullable=False, server_default="PENDING"),
        sa.Column("capture_status", sa.String(40), nullable=False, server_default="NOT_CAPTURED"),
        sa.Column("payment_status", sa.String(40), nullable=False, server_default="PENDING"),
        sa.Column("authorization_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("authorized_at", sa.DateTime(timezone=True), nullable=True), sa.Column("captured_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("create_request_id", sa.String(100), nullable=False, unique=True),
        sa.Column("authorize_request_id", sa.String(100), nullable=False, unique=True),
        sa.Column("capture_request_id", sa.String(100), nullable=False, unique=True),
        sa.Column("paypal_response", sa.JSON(), nullable=True), sa.Column("failure_reason", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    for col in ("id", "milestone_id", "project_id", "client_user_id", "freelancer_user_id", "payment_status"):
        op.create_index(f"ix_paypal_payments_{col}", "paypal_payments", [col])
    op.create_index("ix_paypal_payments_paypal_order_id", "paypal_payments", ["paypal_order_id"], unique=True)
    op.create_index("ix_paypal_payments_authorization_id", "paypal_payments", ["authorization_id"], unique=True)
    op.create_index("ix_paypal_payments_capture_id", "paypal_payments", ["capture_id"], unique=True)

    op.create_table(
        "paypal_webhook_events",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("event_id", sa.String(120), nullable=False),
        sa.Column("event_type", sa.String(120), nullable=False), sa.Column("resource_id", sa.String(120), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False), sa.Column("processed", sa.String(40), nullable=False, server_default="RECEIVED"),
        sa.Column("processing_error", sa.String(1000), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    for col in ("id", "event_type", "resource_id"):
        op.create_index(f"ix_paypal_webhook_events_{col}", "paypal_webhook_events", [col])
    op.create_index("ix_paypal_webhook_events_event_id", "paypal_webhook_events", ["event_id"], unique=True)

    op.create_table(
        "project_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sender_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recipient_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False), sa.Column("off_platform_flag", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("warning_reasons", sa.Text(), nullable=True), sa.Column("attachment_name", sa.String(255), nullable=True),
        sa.Column("attachment_path", sa.Text(), nullable=True), sa.Column("attachment_mime", sa.String(120), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    for col in ("id", "project_id", "sender_id", "recipient_id"):
        op.create_index(f"ix_project_messages_{col}", "project_messages", [col])

    op.create_table(
        "disputes",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("milestone_id", sa.Integer(), sa.ForeignKey("milestones.id", ondelete="CASCADE"), nullable=False),
        sa.Column("raised_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False), sa.Column("status", sa.String(30), nullable=False, server_default="open"),
        sa.Column("ai_report", sa.JSON(), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    for col in ("id", "project_id", "milestone_id", "status"):
        op.create_index(f"ix_disputes_{col}", "disputes", [col])
    op.add_column("disputes", sa.Column("resolution_summary", sa.Text(), nullable=True))
    op.add_column("disputes", sa.Column("resolution_outcome", sa.String(30), nullable=True))
    op.add_column("disputes", sa.Column("resolution_proposed_by", sa.Integer(), nullable=True))
    op.add_column("disputes", sa.Column("client_accepted", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("disputes", sa.Column("freelancer_accepted", sa.Boolean(), nullable=False, server_default=sa.false()))
    with op.batch_alter_table("disputes") as batch_op:
        batch_op.create_foreign_key("fk_disputes_resolution_proposed_by", "users", ["resolution_proposed_by"], ["id"], ondelete="SET NULL")

    op.create_table(
        "dispute_evidence",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("dispute_id", sa.Integer(), sa.ForeignKey("disputes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("submitted_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("description", sa.Text(), nullable=False), sa.Column("file_name", sa.String(255), nullable=True),
        sa.Column("file_path", sa.Text(), nullable=True), sa.Column("mime_type", sa.String(120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    for col in ("id", "dispute_id"):
        op.create_index(f"ix_dispute_evidence_{col}", "dispute_evidence", [col])

    op.create_table(
        "milestone_reminders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("milestone_id", sa.Integer(), sa.ForeignKey("milestones.id", ondelete="CASCADE"), nullable=False),
        sa.Column("submission_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reminder_offset_minutes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("milestone_id", "submission_at", "reminder_offset_minutes", name="uq_milestone_reminder_submission_offset"),
    )
    op.create_index("ix_milestone_reminders_id", "milestone_reminders", ["id"])
    op.create_index("ix_milestone_reminders_milestone_id", "milestone_reminders", ["milestone_id"])

    op.create_table(
        "project_reviews",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reviewer_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reviewee_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False), sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("project_id", "reviewer_id", name="uq_project_review_reviewer"),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_project_review_rating"),
    )
    for col in ("id", "project_id", "reviewer_id", "reviewee_id"):
        op.create_index(f"ix_project_reviews_{col}", "project_reviews", [col])

    # The prior webhook model declared String(20), which truncates reconciliation states.
    with op.batch_alter_table("paypal_webhook_events") as batch_op:
        batch_op.alter_column("processed", type_=sa.String(40), existing_type=sa.String(20), existing_nullable=False)


def downgrade() -> None:
    for table in ("project_reviews", "milestone_reminders", "dispute_evidence", "disputes", "project_messages", "paypal_webhook_events", "paypal_payments", "ai_submission_reviews", "ai_scope_versions", "milestone_audit", "agreement_audit"):
        op.drop_table(table)
    with op.batch_alter_table("milestones") as batch_op:
        batch_op.drop_constraint("fk_milestones_agreement_version", type_="foreignkey")
    for col in ("agreement_version_id", "is_current", "progress_percentage", "deliverables", "completion_criteria", "review_period_days", "review_deadline", "revision_explanation", "approved_at", "updated_at"):
        op.drop_column("milestones", col)
    with op.batch_alter_table("agreements") as batch_op:
        batch_op.drop_constraint("fk_agreements_active_version", type_="foreignkey")
    op.drop_table("agreement_versions")
    op.drop_table("agreements")
