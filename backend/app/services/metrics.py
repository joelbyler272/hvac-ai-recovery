import uuid
from datetime import date, datetime, time

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business import Business
from app.models.call import Call
from app.models.lead import Lead
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.appointment import Appointment
from app.models.daily_metric import DailyMetric


async def compute_daily_metrics(
    db: AsyncSession, business_id: uuid.UUID, for_date: date
) -> dict:
    """Compute and upsert daily metrics for a business."""
    start = datetime.combine(for_date, time.min)
    end = datetime.combine(for_date, time.max)

    total_calls = (
        await db.execute(
            select(func.count(Call.id)).where(
                Call.business_id == business_id,
                Call.created_at >= start,
                Call.created_at <= end,
            )
        )
    ).scalar() or 0

    missed_calls = (
        await db.execute(
            select(func.count(Call.id)).where(
                Call.business_id == business_id,
                Call.status == "missed",
                Call.created_at >= start,
                Call.created_at <= end,
            )
        )
    ).scalar() or 0

    recovered_calls = (
        await db.execute(
            select(func.count(Conversation.id)).where(
                Conversation.business_id == business_id,
                Conversation.call_id.isnot(None),
                Conversation.created_at >= start,
                Conversation.created_at <= end,
            )
        )
    ).scalar() or 0

    leads_captured = (
        await db.execute(
            select(func.count(Lead.id)).where(
                Lead.business_id == business_id,
                Lead.created_at >= start,
                Lead.created_at <= end,
            )
        )
    ).scalar() or 0

    leads_qualified = (
        await db.execute(
            select(func.count(Lead.id)).where(
                Lead.business_id == business_id,
                Lead.status.in_(["qualified", "booked", "completed"]),
                Lead.updated_at >= start,
                Lead.updated_at <= end,
            )
        )
    ).scalar() or 0

    appointments_booked = (
        await db.execute(
            select(func.count(Appointment.id)).where(
                Appointment.business_id == business_id,
                Appointment.created_at >= start,
                Appointment.created_at <= end,
            )
        )
    ).scalar() or 0

    messages_sent = (
        await db.execute(
            select(func.count(Message.id)).where(
                Message.business_id == business_id,
                Message.direction == "outbound",
                Message.created_at >= start,
                Message.created_at <= end,
            )
        )
    ).scalar() or 0

    messages_received = (
        await db.execute(
            select(func.count(Message.id)).where(
                Message.business_id == business_id,
                Message.direction == "inbound",
                Message.created_at >= start,
                Message.created_at <= end,
            )
        )
    ).scalar() or 0

    # Estimated revenue
    biz = (
        await db.execute(
            select(Business.avg_job_value).where(Business.id == business_id)
        )
    ).scalar() or 350
    estimated_revenue = float(biz) * leads_qualified

    metrics = {
        "total_calls": total_calls,
        "missed_calls": missed_calls,
        "recovered_calls": recovered_calls,
        "leads_captured": leads_captured,
        "leads_qualified": leads_qualified,
        "appointments_booked": appointments_booked,
        "estimated_revenue": estimated_revenue,
        "messages_sent": messages_sent,
        "messages_received": messages_received,
    }

    # Upsert into DailyMetric
    existing = await db.execute(
        select(DailyMetric).where(
            DailyMetric.business_id == business_id,
            DailyMetric.date == for_date,
        )
    )
    dm = existing.scalar_one_or_none()

    if dm:
        await db.execute(
            update(DailyMetric).where(DailyMetric.id == dm.id).values(**metrics)
        )
    else:
        dm = DailyMetric(business_id=business_id, date=for_date, **metrics)
        db.add(dm)

    await db.flush()
    return metrics
