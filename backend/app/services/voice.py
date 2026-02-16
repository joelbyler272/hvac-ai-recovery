import uuid
from datetime import datetime

import pytz

from app.models.business import Business
from app.models.call import Call
from app.models.lead import Lead
from app.models.conversation import Conversation


async def get_business_by_twilio_number(twilio_number: str) -> Business | None:
    """Look up business by their Twilio phone number."""
    # TODO: Implement DB query
    return None


async def create_call_record(
    business_id: uuid.UUID,
    twilio_call_sid: str,
    caller_phone: str,
    status: str,
    is_after_hours: bool,
) -> Call:
    """Create a call record in the database."""
    # TODO: Implement DB insert
    call = Call()
    call.id = uuid.uuid4()
    call.business_id = business_id
    call.twilio_call_sid = twilio_call_sid
    call.caller_phone = caller_phone
    call.status = status
    call.is_after_hours = is_after_hours
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


async def get_call(call_id: str) -> Call:
    """Get a call record by ID."""
    # TODO: Implement DB query
    return Call()


async def update_call(call_id: uuid.UUID, status: str, duration: int = 0) -> None:
    """Update a call record."""
    # TODO: Implement DB update
    pass


async def is_opted_out(phone: str, business_id: uuid.UUID) -> bool:
    """Check if a phone number has opted out."""
    # TODO: Implement DB query
    return False


async def get_active_conversation(
    business_id: uuid.UUID, phone: str
) -> Conversation | None:
    """Find an active conversation for a phone number and business."""
    # TODO: Implement DB query
    return None


async def create_or_get_lead(
    business_id: uuid.UUID, phone: str, source: str
) -> Lead:
    """Create a new lead or get existing one."""
    # TODO: Implement DB upsert
    lead = Lead()
    lead.id = uuid.uuid4()
    lead.business_id = business_id
    lead.phone = phone
    lead.source = source
    return lead


async def create_conversation(
    business_id: uuid.UUID,
    lead_id: uuid.UUID,
    call_id: uuid.UUID | None = None,
) -> Conversation:
    """Create a new conversation."""
    # TODO: Implement DB insert
    conversation = Conversation()
    conversation.id = uuid.uuid4()
    conversation.business_id = business_id
    conversation.lead_id = lead_id
    conversation.call_id = call_id
    conversation.status = "active"
    return conversation
