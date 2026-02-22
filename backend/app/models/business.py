import uuid
from datetime import datetime

from sqlalchemy import String, Text, ARRAY, DECIMAL, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    owner_name: Mapped[str] = mapped_column(Text, nullable=False)
    owner_email: Mapped[str] = mapped_column(Text, nullable=False)
    owner_phone: Mapped[str] = mapped_column(Text, nullable=False)
    business_phone: Mapped[str] = mapped_column(Text, nullable=False)
    twilio_number: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    timezone: Mapped[str] = mapped_column(
        Text, nullable=False, default="America/New_York"
    )
    business_hours: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=lambda: {
            "monday": {"open": "08:00", "close": "17:00"},
            "tuesday": {"open": "08:00", "close": "17:00"},
            "wednesday": {"open": "08:00", "close": "17:00"},
            "thursday": {"open": "08:00", "close": "17:00"},
            "friday": {"open": "08:00", "close": "17:00"},
            "saturday": None,
            "sunday": None,
        },
    )
    services: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )
    avg_job_value: Mapped[float] = mapped_column(
        DECIMAL(10, 2), default=350.00
    )
    ai_greeting: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    notification_prefs: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=lambda: {
            "sms": True,
            "email": True,
            "quiet_start": "21:00",
            "quiet_end": "07:00",
        },
    )
    subscription_status: Mapped[str] = mapped_column(
        Text, nullable=False, default="active"
    )
    stripe_customer_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    supabase_user_id: Mapped[str | None] = mapped_column(
        Text, unique=True, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
