import uuid
from datetime import datetime

import pytz
from sqlalchemy import select, update, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business import Business
from app.models.call import Call
from app.models.lead import Lead
from app.models.conversation import Conversation
from app.models.opt_out import OptOut


async def get_business_by_twilio_number(
    db: AsyncSession, twilio_number: str
) -> Business | None:
    """Look up business by their Twilio phone number."""
    result = await db.execute(
        select(Business).where(Business.twilio_number == twilio_number)
    )
    return result.scalar_one_or_none()


async def create_call_record(
    db: AsyncSession,
    business_id: uuid.UUID,
    twilio_call_sid: str,
    caller_phone: str,
    status: str,
    is_after_hours: bool,
) -> Call:
    """Create a call record in the database."""
    call = Call(
        business_id=business_id,
        twilio_call_sid=twilio_call_sid,
        caller_phone=caller_phone,
        status=status,
        is_after_hours=is_after_hours,
    )
    db.add(call)
    await db.flush()
    return call


def is_after_hours(business: Business) -> bool:
    """Check if current time is outside business hours."""
    now = datetime.now(pytz.timezone(business.timezone))
    day = now.strftime("%A").lower()
    hours = business.business_hours.get(day)

    if not hours:
        return True

    open_time = datetime.strptime(hours["open"], "%H:%M").time()
    close_time = datetime.strptime(hours["close"], "%H:%M").time()
    return not (open_time <= now.time() <= close_time)


async def get_call(db: AsyncSession, call_id: str) -> Call | None:
    """Get a call record by ID."""
    result = await db.execute(
        select(Call).where(Call.id == uuid.UUID(call_id))
    )
    return result.scalar_one_or_none()


async def update_call(
    db: AsyncSession, call_id: uuid.UUID, status: str, duration: int = 0
) -> None:
    """Update a call record."""
    await db.execute(
        update(Call)
        .where(Call.id == call_id)
        .values(status=status, duration_seconds=duration)
    )
    await db.flush()


async def is_opted_out(
    db: AsyncSession, phone: str, business_id: uuid.UUID
) -> bool:
    """Check if a phone number has opted out (business-specific or global)."""
    result = await db.execute(
        select(OptOut.id).where(
            OptOut.phone == phone,
            or_(OptOut.business_id == business_id, OptOut.business_id.is_(None)),
        )
    )
    return result.scalar_one_or_none() is not None


async def get_active_conversation(
    db: AsyncSession, business_id: uuid.UUID, phone: str
) -> Conversation | None:
    """Find an active conversation for a phone number and business."""
    result = await db.execute(
        select(Conversation)
        .join(Lead, Conversation.lead_id == Lead.id)
        .where(
            Conversation.business_id == business_id,
            Lead.phone == phone,
            Conversation.status.in_(["active", "follow_up", "human_active"]),
        )
        .order_by(Conversation.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def create_or_get_lead(
    db: AsyncSession,
    business_id: uuid.UUID,
    phone: str,
    source: str,
) -> Lead:
    """Create a new lead or get existing one."""
    result = await db.execute(
        select(Lead).where(Lead.business_id == business_id, Lead.phone == phone)
    )
    lead = result.scalar_one_or_none()
    if lead:
        return lead

    lead = Lead(
        business_id=business_id,
        phone=phone,
        source=source,
        status="new",
    )
    db.add(lead)
    await db.flush()
    return lead


async def create_conversation(
    db: AsyncSession,
    business_id: uuid.UUID,
    lead_id: uuid.UUID,
    call_id: uuid.UUID | None = None,
) -> Conversation:
    """Create a new conversation."""
    conversation = Conversation(
        business_id=business_id,
        lead_id=lead_id,
        call_id=call_id,
        status="active",
    )
    db.add(conversation)
    await db.flush()
    return conversation
