import uuid
from datetime import datetime, date

from sqlalchemy import Integer, Date, DECIMAL, ForeignKey, TIMESTAMP, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DailyMetric(Base):
    __tablename__ = "daily_metrics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    total_calls: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    missed_calls: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    recovered_calls: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    leads_captured: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    leads_qualified: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    appointments_booked: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    estimated_revenue: Mapped[float] = mapped_column(
        DECIMAL(10, 2), nullable=False, default=0
    )
    messages_sent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    messages_received: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("business_id", "date", name="uq_metric_business_date"),
    )
