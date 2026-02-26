import uuid
from datetime import datetime

from sqlalchemy import Text, Integer, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class VoiceAIConfig(Base):
    __tablename__ = "voice_ai_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("businesses.id"), unique=True, nullable=False
    )
    provider: Mapped[str] = mapped_column(Text, nullable=False, default="vapi")
    provider_assistant_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    system_prompt_override: Mapped[str | None] = mapped_column(Text, nullable=True)
    voice_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    greeting_override: Mapped[str | None] = mapped_column(Text, nullable=True)
    max_call_duration_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False, default=300
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
