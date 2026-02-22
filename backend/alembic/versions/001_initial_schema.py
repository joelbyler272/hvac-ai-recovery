"""Initial schema — all core tables

Revision ID: 001
Revises: None
Create Date: 2026-02-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Businesses ────────────────────────────────────────────────────
    op.create_table(
        "businesses",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("owner_name", sa.Text(), nullable=False),
        sa.Column("owner_email", sa.Text(), nullable=False),
        sa.Column("owner_phone", sa.Text(), nullable=False),
        sa.Column("business_phone", sa.Text(), nullable=False),
        sa.Column("twilio_number", sa.Text(), nullable=False, unique=True),
        sa.Column("timezone", sa.Text(), nullable=False, server_default="America/New_York"),
        sa.Column("business_hours", JSONB(), nullable=False, server_default=sa.text(
            "'{}'::jsonb"
        )),
        sa.Column("services", ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("avg_job_value", sa.DECIMAL(10, 2), server_default="350.00"),
        sa.Column("ai_greeting", sa.Text(), nullable=True),
        sa.Column("ai_instructions", sa.Text(), nullable=True),
        sa.Column("notification_prefs", JSONB(), nullable=False, server_default=sa.text(
            "'{}'::jsonb"
        )),
        sa.Column("subscription_status", sa.Text(), nullable=False, server_default="active"),
        sa.Column("stripe_customer_id", sa.Text(), nullable=True),
        sa.Column("stripe_subscription_id", sa.Text(), nullable=True),
        sa.Column("supabase_user_id", sa.Text(), nullable=True, unique=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ── Calls ─────────────────────────────────────────────────────────
    op.create_table(
        "calls",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("business_id", UUID(as_uuid=True), sa.ForeignKey("businesses.id"), nullable=False),
        sa.Column("twilio_call_sid", sa.Text(), nullable=False, unique=True),
        sa.Column("caller_phone", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="ringing"),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("is_after_hours", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("recording_url", sa.Text(), nullable=True),
        sa.Column("transcription", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_calls_business", "calls", ["business_id", sa.text("created_at DESC")])
    op.create_index("idx_calls_caller", "calls", ["caller_phone", "business_id"])

    # ── Leads ─────────────────────────────────────────────────────────
    op.create_table(
        "leads",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("business_id", UUID(as_uuid=True), sa.ForeignKey("businesses.id"), nullable=False),
        sa.Column("phone", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("service_needed", sa.Text(), nullable=True),
        sa.Column("urgency", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="new"),
        sa.Column("source", sa.Text(), nullable=False, server_default="missed_call"),
        sa.Column("estimated_value", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("preferred_time", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("business_id", "phone", name="uq_lead_business_phone"),
    )
    op.create_index("idx_leads_business_status", "leads", ["business_id", "status"])

    # ── Conversations ─────────────────────────────────────────────────
    op.create_table(
        "conversations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("business_id", UUID(as_uuid=True), sa.ForeignKey("businesses.id"), nullable=False),
        sa.Column("lead_id", UUID(as_uuid=True), sa.ForeignKey("leads.id"), nullable=False),
        sa.Column("call_id", UUID(as_uuid=True), sa.ForeignKey("calls.id"), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        sa.Column("follow_up_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_follow_up_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("qualification_data", JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_convos_business", "conversations", ["business_id", "status"])
    op.create_index(
        "idx_convos_followup",
        "conversations",
        ["next_follow_up_at"],
        postgresql_where=sa.text("status = 'follow_up'"),
    )

    # ── Messages ──────────────────────────────────────────────────────
    op.create_table(
        "messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("conversation_id", UUID(as_uuid=True), sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("business_id", UUID(as_uuid=True), sa.ForeignKey("businesses.id"), nullable=False),
        sa.Column("direction", sa.Text(), nullable=False),
        sa.Column("sender_type", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("twilio_message_sid", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="sent"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_messages_convo", "messages", ["conversation_id", sa.text("created_at ASC")])

    # ── Appointments ──────────────────────────────────────────────────
    op.create_table(
        "appointments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("business_id", UUID(as_uuid=True), sa.ForeignKey("businesses.id"), nullable=False),
        sa.Column("lead_id", UUID(as_uuid=True), sa.ForeignKey("leads.id"), nullable=False),
        sa.Column("conversation_id", UUID(as_uuid=True), sa.ForeignKey("conversations.id"), nullable=True),
        sa.Column("scheduled_date", sa.Date(), nullable=False),
        sa.Column("scheduled_time", sa.Time(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("service_type", sa.Text(), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="scheduled"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_appointments_business", "appointments", ["business_id", "scheduled_date"])

    # ── Review Requests ───────────────────────────────────────────────
    op.create_table(
        "review_requests",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("business_id", UUID(as_uuid=True), sa.ForeignKey("businesses.id"), nullable=False),
        sa.Column("lead_id", UUID(as_uuid=True), sa.ForeignKey("leads.id"), nullable=False),
        sa.Column("phone", sa.Text(), nullable=False),
        sa.Column("review_url", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("sent_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("reminder_sent_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ── Opt-Outs ──────────────────────────────────────────────────────
    op.create_table(
        "opt_outs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("phone", sa.Text(), nullable=False),
        sa.Column("business_id", UUID(as_uuid=True), sa.ForeignKey("businesses.id"), nullable=True),
        sa.Column("reason", sa.Text(), server_default="stop_keyword"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("phone", "business_id", name="uq_opt_out_phone_business"),
    )
    op.create_index("idx_opt_outs_phone", "opt_outs", ["phone"])

    # ── Audit Log ─────────────────────────────────────────────────────
    op.create_table(
        "audit_log",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("business_id", UUID(as_uuid=True), sa.ForeignKey("businesses.id"), nullable=True),
        sa.Column("entity_type", sa.Text(), nullable=False),
        sa.Column("entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("details", JSONB(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_audit_business", "audit_log", ["business_id", sa.text("created_at DESC")])

    # ── Daily Metrics ─────────────────────────────────────────────────
    op.create_table(
        "daily_metrics",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("business_id", UUID(as_uuid=True), sa.ForeignKey("businesses.id"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("total_calls", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("missed_calls", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("recovered_calls", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("leads_captured", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("leads_qualified", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("appointments_booked", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_revenue", sa.DECIMAL(10, 2), nullable=False, server_default="0"),
        sa.Column("messages_sent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("messages_received", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("business_id", "date", name="uq_daily_metrics_business_date"),
    )


def downgrade() -> None:
    op.drop_table("daily_metrics")
    op.drop_table("audit_log")
    op.drop_table("opt_outs")
    op.drop_table("review_requests")
    op.drop_table("appointments")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("leads")
    op.drop_table("calls")
    op.drop_table("businesses")
