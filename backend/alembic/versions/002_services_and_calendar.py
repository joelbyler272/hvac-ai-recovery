"""Add services table, calendar_integrations table, and appointment columns

Revision ID: 002
Revises: 001
Create Date: 2026-02-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Services ─────────────────────────────────────────────────────
    op.create_table(
        "services",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("business_id", UUID(as_uuid=True), sa.ForeignKey("businesses.id"), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("is_bookable", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("business_id", "name", name="uq_service_business_name"),
    )
    op.create_index("idx_services_business_active", "services", ["business_id", "is_active"])

    # ── Calendar Integrations ────────────────────────────────────────
    op.create_table(
        "calendar_integrations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("business_id", UUID(as_uuid=True), sa.ForeignKey("businesses.id"), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("access_token", sa.Text(), nullable=False),
        sa.Column("refresh_token", sa.Text(), nullable=False),
        sa.Column("token_expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("calendar_id", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_sync_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("business_id", "provider", name="uq_calendar_business_provider"),
    )

    # ── Appointment columns ──────────────────────────────────────────
    op.add_column("appointments", sa.Column("service_id", UUID(as_uuid=True), sa.ForeignKey("services.id"), nullable=True))
    op.add_column("appointments", sa.Column("calendar_event_id", sa.Text(), nullable=True))

    # ── Data migration: convert business.services string array → Service rows ──
    conn = op.get_bind()
    businesses = conn.execute(sa.text("SELECT id, services FROM businesses WHERE services IS NOT NULL AND array_length(services, 1) > 0"))
    for row in businesses:
        biz_id = row[0]
        service_names = row[1]
        for idx, name in enumerate(service_names):
            if name and name.strip():
                conn.execute(
                    sa.text(
                        "INSERT INTO services (id, business_id, name, is_bookable, duration_minutes, sort_order) "
                        "VALUES (gen_random_uuid(), :biz_id, :name, false, 60, :sort_order) "
                        "ON CONFLICT (business_id, name) DO NOTHING"
                    ),
                    {"biz_id": biz_id, "name": name.strip(), "sort_order": idx},
                )


def downgrade() -> None:
    op.drop_column("appointments", "calendar_event_id")
    op.drop_column("appointments", "service_id")
    op.drop_table("calendar_integrations")
    op.drop_index("idx_services_business_active", table_name="services")
    op.drop_table("services")
