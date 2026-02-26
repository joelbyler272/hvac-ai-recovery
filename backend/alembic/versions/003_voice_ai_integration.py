"""Add voice AI columns, voice_ai_configs table, and owner_nudges table

Revision ID: 003
Revises: 002
Create Date: 2026-02-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Calls: voice AI tracking columns ─────────────────────────────
    op.add_column("calls", sa.Column("voice_ai_used", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("calls", sa.Column("voice_ai_transcript", sa.Text(), nullable=True))
    op.add_column("calls", sa.Column("voice_ai_duration_seconds", sa.Integer(), nullable=True))
    op.add_column("calls", sa.Column("voice_ai_cost", sa.DECIMAL(10, 4), nullable=True))
    op.add_column("calls", sa.Column("line_type", sa.Text(), nullable=False, server_default="unknown"))
    op.add_column("calls", sa.Column("vapi_call_id", sa.Text(), nullable=True))

    # ── Leads: qualification source ──────────────────────────────────
    op.add_column("leads", sa.Column("qualification_source", sa.Text(), nullable=False, server_default="sms"))

    # ── Conversations: channel + voice transcript ────────────────────
    op.add_column("conversations", sa.Column("channel", sa.Text(), nullable=False, server_default="sms"))
    op.add_column("conversations", sa.Column("voice_transcript", sa.Text(), nullable=True))

    # ── Businesses: voice AI config ──────────────────────────────────
    op.add_column("businesses", sa.Column("vapi_assistant_id", sa.Text(), nullable=True))
    op.add_column("businesses", sa.Column("google_place_id", sa.Text(), nullable=True))
    op.add_column("businesses", sa.Column("call_recording_enabled", sa.Boolean(), nullable=False, server_default="true"))
    op.add_column("businesses", sa.Column("two_party_consent_state", sa.Boolean(), nullable=False, server_default="false"))

    # ── Voice AI Configs table ───────────────────────────────────────
    op.create_table(
        "voice_ai_configs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("business_id", UUID(as_uuid=True), sa.ForeignKey("businesses.id"), nullable=False, unique=True),
        sa.Column("provider", sa.Text(), nullable=False, server_default="vapi"),
        sa.Column("provider_assistant_id", sa.Text(), nullable=True),
        sa.Column("system_prompt_override", sa.Text(), nullable=True),
        sa.Column("voice_id", sa.Text(), nullable=True),
        sa.Column("greeting_override", sa.Text(), nullable=True),
        sa.Column("max_call_duration_seconds", sa.Integer(), nullable=False, server_default="300"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    # ── Owner Nudges table ───────────────────────────────────────────
    op.create_table(
        "owner_nudges",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("business_id", UUID(as_uuid=True), sa.ForeignKey("businesses.id"), nullable=False),
        sa.Column("lead_id", UUID(as_uuid=True), sa.ForeignKey("leads.id"), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("sent_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("acknowledged_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("status IN ('pending', 'sent', 'acknowledged')", name="ck_owner_nudge_status"),
    )
    op.create_index("idx_nudges_business_lead", "owner_nudges", ["business_id", "lead_id"])


def downgrade() -> None:
    op.drop_table("owner_nudges")
    op.drop_table("voice_ai_configs")

    op.drop_column("businesses", "two_party_consent_state")
    op.drop_column("businesses", "call_recording_enabled")
    op.drop_column("businesses", "google_place_id")
    op.drop_column("businesses", "vapi_assistant_id")

    op.drop_column("conversations", "voice_transcript")
    op.drop_column("conversations", "channel")

    op.drop_column("leads", "qualification_source")

    op.drop_column("calls", "vapi_call_id")
    op.drop_column("calls", "line_type")
    op.drop_column("calls", "voice_ai_cost")
    op.drop_column("calls", "voice_ai_duration_seconds")
    op.drop_column("calls", "voice_ai_transcript")
    op.drop_column("calls", "voice_ai_used")
