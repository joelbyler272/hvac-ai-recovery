import uuid
from datetime import datetime

from sqlalchemy import Text, Integer, Boolean, ForeignKey, TIMESTAMP, Index, DECIMAL
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Call(Base):
    __tablename__ = "calls"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False
    )
    twilio_call_sid: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    caller_phone: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="ringing")
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_after_hours: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recording_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    transcription: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow
    )

    # Voice AI fields
    voice_ai_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    voice_ai_transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    voice_ai_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    voice_ai_cost: Mapped[float | None] = mapped_column(DECIMAL(10, 4), nullable=True)
    line_type: Mapped[str] = mapped_column(Text, nullable=False, default="unknown")
    vapi_call_id: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("idx_calls_business", "business_id", "created_at"),
        Index("idx_calls_caller", "caller_phone", "business_id"),
    )
