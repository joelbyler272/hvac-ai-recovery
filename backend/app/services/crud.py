"""Centralized CRUD operations for API endpoints."""
import uuid
from datetime import date, time, datetime, timedelta

from sqlalchemy import select, update, func, or_, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business import Business
from app.models.call import Call
from app.models.lead import Lead
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.appointment import Appointment
from app.models.daily_metric import DailyMetric
from app.models.audit_log import AuditLog
from app.models.review_request import ReviewRequest
from app.models.service import Service


# ── Leads ──────────────────────────────────────────────────────────────


async def get_leads(
    db: AsyncSession,
    business_id: uuid.UUID,
    status: str | None = None,
    page: int = 1,
    per_page: int = 50,
) -> list[Lead]:
    offset = (page - 1) * per_page
    query = (
        select(Lead)
        .where(Lead.business_id == business_id)
        .order_by(Lead.updated_at.desc())
        .limit(per_page)
        .offset(offset)
    )
    if status:
        query = query.where(Lead.status == status)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_lead_detail(
    db: AsyncSession, business_id: uuid.UUID, lead_id: uuid.UUID
) -> tuple[Lead, list[Conversation], list[Message]] | None:
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id, Lead.business_id == business_id)
    )
    lead = result.scalar_one_or_none()
    if not lead:
        return None

    convos_result = await db.execute(
        select(Conversation)
        .where(Conversation.lead_id == lead_id, Conversation.business_id == business_id)
        .order_by(Conversation.created_at.desc())
    )
    conversations = list(convos_result.scalars().all())

    msgs_result = await db.execute(
        select(Message)
        .where(
            Message.conversation_id.in_(
                select(Conversation.id).where(
                    Conversation.lead_id == lead_id,
                    Conversation.business_id == business_id,
                )
            )
        )
        .order_by(Message.created_at.asc())
    )
    messages = list(msgs_result.scalars().all())

    return lead, conversations, messages


async def get_lead_by_id(
    db: AsyncSession, business_id: uuid.UUID, lead_id: uuid.UUID
) -> Lead | None:
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id, Lead.business_id == business_id)
    )
    return result.scalar_one_or_none()


async def update_lead(
    db: AsyncSession, business_id: uuid.UUID, lead_id: uuid.UUID, **fields
) -> Lead | None:
    fields["updated_at"] = datetime.utcnow()
    await db.execute(
        update(Lead)
        .where(Lead.id == lead_id, Lead.business_id == business_id)
        .values(**fields)
    )
    await db.flush()
    return await get_lead_by_id(db, business_id, lead_id)


# ── Conversations ──────────────────────────────────────────────────────


async def get_conversations(
    db: AsyncSession,
    business_id: uuid.UUID,
    status: str | None = None,
) -> list[tuple[Conversation, Lead]]:
    query = (
        select(Conversation, Lead)
        .join(Lead, Conversation.lead_id == Lead.id)
        .where(Conversation.business_id == business_id)
        .order_by(Conversation.updated_at.desc())
    )
    if status:
        query = query.where(Conversation.status == status)
    result = await db.execute(query)
    return list(result.all())


async def get_conversation_detail(
    db: AsyncSession, business_id: uuid.UUID, conversation_id: uuid.UUID
) -> Conversation | None:
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.business_id == business_id,
        )
    )
    return result.scalar_one_or_none()


async def get_conversation_messages(
    db: AsyncSession, conversation_id: uuid.UUID
) -> list[Message]:
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    return list(result.scalars().all())


async def update_conversation_status(
    db: AsyncSession,
    business_id: uuid.UUID,
    conversation_id: uuid.UUID,
    status: str,
) -> Conversation | None:
    await db.execute(
        update(Conversation)
        .where(
            Conversation.id == conversation_id,
            Conversation.business_id == business_id,
        )
        .values(status=status, updated_at=datetime.utcnow())
    )
    await db.flush()
    return await get_conversation_detail(db, business_id, conversation_id)


# ── Calls ──────────────────────────────────────────────────────────────


async def get_calls(
    db: AsyncSession,
    business_id: uuid.UUID,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Call]:
    query = (
        select(Call)
        .where(Call.business_id == business_id)
        .order_by(Call.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if status:
        query = query.where(Call.status == status)
    result = await db.execute(query)
    return list(result.scalars().all())


# ── Appointments ───────────────────────────────────────────────────────


async def get_appointments(
    db: AsyncSession,
    business_id: uuid.UUID,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[Appointment]:
    query = (
        select(Appointment)
        .where(Appointment.business_id == business_id)
        .order_by(Appointment.scheduled_date.asc(), Appointment.scheduled_time.asc())
    )
    if date_from:
        query = query.where(Appointment.scheduled_date >= date_from)
    if date_to:
        query = query.where(Appointment.scheduled_date <= date_to)
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_appointment(
    db: AsyncSession,
    business_id: uuid.UUID,
    lead_id: uuid.UUID,
    scheduled_date: date,
    scheduled_time: time,
    conversation_id: uuid.UUID | None = None,
    service_type: str | None = None,
    address: str | None = None,
    notes: str | None = None,
    duration_minutes: int = 60,
) -> Appointment:
    appt = Appointment(
        business_id=business_id,
        lead_id=lead_id,
        conversation_id=conversation_id,
        scheduled_date=scheduled_date,
        scheduled_time=scheduled_time,
        duration_minutes=duration_minutes,
        service_type=service_type,
        address=address,
        notes=notes,
        status="scheduled",
    )
    db.add(appt)
    await db.flush()
    return appt


async def update_appointment(
    db: AsyncSession,
    business_id: uuid.UUID,
    appointment_id: uuid.UUID,
    **fields,
) -> Appointment | None:
    fields["updated_at"] = datetime.utcnow()
    await db.execute(
        update(Appointment)
        .where(
            Appointment.id == appointment_id,
            Appointment.business_id == business_id,
        )
        .values(**fields)
    )
    await db.flush()
    result = await db.execute(
        select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.business_id == business_id,
        )
    )
    return result.scalar_one_or_none()


# ── Dashboard ──────────────────────────────────────────────────────────


async def get_dashboard_stats(
    db: AsyncSession, business_id: uuid.UUID
) -> dict:
    today = date.today()
    month_start = today.replace(day=1)

    async def _stats_for_period(start: date, end: date) -> dict:
        # Total calls
        total_calls = (
            await db.execute(
                select(func.count(Call.id)).where(
                    Call.business_id == business_id,
                    func.cast(Call.created_at, func.date_trunc("day", Call.created_at)).isnot(None),
                    Call.created_at >= datetime.combine(start, time.min),
                    Call.created_at <= datetime.combine(end, time.max),
                )
            )
        ).scalar() or 0

        # Missed calls
        missed_calls = (
            await db.execute(
                select(func.count(Call.id)).where(
                    Call.business_id == business_id,
                    Call.status == "missed",
                    Call.created_at >= datetime.combine(start, time.min),
                    Call.created_at <= datetime.combine(end, time.max),
                )
            )
        ).scalar() or 0

        # Recovered: missed calls that have an associated conversation
        recovered_calls = (
            await db.execute(
                select(func.count(Conversation.id)).where(
                    Conversation.business_id == business_id,
                    Conversation.call_id.isnot(None),
                    Conversation.created_at >= datetime.combine(start, time.min),
                    Conversation.created_at <= datetime.combine(end, time.max),
                )
            )
        ).scalar() or 0

        # Leads qualified
        leads_qualified = (
            await db.execute(
                select(func.count(Lead.id)).where(
                    Lead.business_id == business_id,
                    Lead.status.in_(["qualified", "booked", "completed"]),
                    Lead.updated_at >= datetime.combine(start, time.min),
                    Lead.updated_at <= datetime.combine(end, time.max),
                )
            )
        ).scalar() or 0

        # Appointments booked
        appointments_booked = (
            await db.execute(
                select(func.count(Appointment.id)).where(
                    Appointment.business_id == business_id,
                    Appointment.created_at >= datetime.combine(start, time.min),
                    Appointment.created_at <= datetime.combine(end, time.max),
                )
            )
        ).scalar() or 0

        # Estimated revenue
        biz = await db.execute(
            select(Business.avg_job_value).where(Business.id == business_id)
        )
        avg_value = float(biz.scalar() or 350)
        estimated_revenue = leads_qualified * avg_value

        return {
            "total_calls": total_calls,
            "missed_calls": missed_calls,
            "recovered_calls": recovered_calls,
            "leads_qualified": leads_qualified,
            "appointments_booked": appointments_booked,
            "estimated_revenue": estimated_revenue,
        }

    return {
        "today": await _stats_for_period(today, today),
        "this_month": await _stats_for_period(month_start, today),
    }


async def get_recent_activity(
    db: AsyncSession, business_id: uuid.UUID, limit: int = 20
) -> list[dict]:
    """Get recent activity — calls and messages merged by time."""
    from app.api.schemas import activity_to_dict

    recent_calls = await db.execute(
        select(Call)
        .where(Call.business_id == business_id)
        .order_by(Call.created_at.desc())
        .limit(limit)
    )
    recent_messages = await db.execute(
        select(Message)
        .where(Message.business_id == business_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )

    items = []
    for call in recent_calls.scalars().all():
        items.append(("call", call, call.created_at))
    for msg in recent_messages.scalars().all():
        items.append(("message", msg, msg.created_at))

    items.sort(key=lambda x: x[2], reverse=True)
    return [activity_to_dict(t, item) for t, item, _ in items[:limit]]


# ── Metrics / Reports ──────────────────────────────────────────────────


async def get_daily_metrics_range(
    db: AsyncSession,
    business_id: uuid.UUID,
    date_from: date,
    date_to: date,
) -> list[DailyMetric]:
    result = await db.execute(
        select(DailyMetric)
        .where(
            DailyMetric.business_id == business_id,
            DailyMetric.date >= date_from,
            DailyMetric.date <= date_to,
        )
        .order_by(DailyMetric.date.asc())
    )
    return list(result.scalars().all())


# ── Business ───────────────────────────────────────────────────────────


async def get_business(
    db: AsyncSession, business_id: uuid.UUID
) -> Business | None:
    result = await db.execute(
        select(Business).where(Business.id == business_id)
    )
    return result.scalar_one_or_none()


async def update_business(
    db: AsyncSession, business_id: uuid.UUID, **fields
) -> None:
    fields["updated_at"] = datetime.utcnow()
    await db.execute(
        update(Business)
        .where(Business.id == business_id)
        .values(**fields)
    )
    await db.flush()


# ── Services ──────────────────────────────────────────────────────────


async def get_services(
    db: AsyncSession, business_id: uuid.UUID
) -> list[Service]:
    result = await db.execute(
        select(Service)
        .where(Service.business_id == business_id, Service.is_active == True)
        .order_by(Service.sort_order.asc(), Service.name.asc())
    )
    return list(result.scalars().all())


async def get_service(
    db: AsyncSession, business_id: uuid.UUID, service_id: uuid.UUID
) -> Service | None:
    result = await db.execute(
        select(Service).where(
            Service.id == service_id,
            Service.business_id == business_id,
        )
    )
    return result.scalar_one_or_none()


async def create_service(
    db: AsyncSession,
    business_id: uuid.UUID,
    name: str,
    price: float | None = None,
    duration_minutes: int = 60,
    is_bookable: bool = False,
    description: str | None = None,
    sort_order: int = 0,
) -> Service:
    svc = Service(
        business_id=business_id,
        name=name,
        description=description,
        price=price,
        duration_minutes=duration_minutes,
        is_bookable=is_bookable,
        sort_order=sort_order,
    )
    db.add(svc)
    await db.flush()
    return svc


async def update_service(
    db: AsyncSession,
    business_id: uuid.UUID,
    service_id: uuid.UUID,
    **fields,
) -> Service | None:
    fields["updated_at"] = datetime.utcnow()
    await db.execute(
        update(Service)
        .where(Service.id == service_id, Service.business_id == business_id)
        .values(**fields)
    )
    await db.flush()
    return await get_service(db, business_id, service_id)


async def delete_service(
    db: AsyncSession,
    business_id: uuid.UUID,
    service_id: uuid.UUID,
) -> bool:
    """Soft-delete a service (set is_active=False)."""
    result = await db.execute(
        update(Service)
        .where(Service.id == service_id, Service.business_id == business_id)
        .values(is_active=False, updated_at=datetime.utcnow())
    )
    await db.flush()
    return result.rowcount > 0


async def reorder_services(
    db: AsyncSession,
    business_id: uuid.UUID,
    order: list[dict],
) -> None:
    """Bulk update sort_order. order = [{"id": "...", "sort_order": 0}, ...]"""
    for item in order:
        await db.execute(
            update(Service)
            .where(
                Service.id == uuid.UUID(item["id"]),
                Service.business_id == business_id,
            )
            .values(sort_order=item["sort_order"])
        )
    await db.flush()


# ── Audit Log ──────────────────────────────────────────────────────────


async def create_audit_log(
    db: AsyncSession,
    business_id: uuid.UUID | None,
    entity_type: str,
    entity_id: uuid.UUID,
    action: str,
    details: dict | None = None,
) -> None:
    log = AuditLog(
        business_id=business_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        details=details,
    )
    db.add(log)
    await db.flush()
