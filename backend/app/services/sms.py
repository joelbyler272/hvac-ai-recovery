import uuid
import logging

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from twilio.rest import Client

from app.config import get_settings
from app.models.message import Message
from app.models.opt_out import OptOut
from app.models.conversation import Conversation
from app.models.lead import Lead

logger = logging.getLogger(__name__)
settings = get_settings()

# Lazy init — only create client when credentials exist
_twilio_client: Client | None = None


def _get_twilio_client() -> Client:
    global _twilio_client
    if _twilio_client is None:
        _twilio_client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    return _twilio_client


async def send_sms(
    db: AsyncSession,
    to: str,
    from_: str,
    body: str,
    conversation_id: uuid.UUID,
    business_id: uuid.UUID,
    sender_type: str = "ai",
) -> str:
    """Send an SMS via Twilio and save to database."""
    client = _get_twilio_client()
    message = client.messages.create(
        to=to,
        from_=from_,
        body=body,
        status_callback=f"{settings.base_url}/webhook/sms/status",
    )

    await save_message(
        db=db,
        conversation_id=conversation_id,
        business_id=business_id,
        direction="outbound",
        sender_type=sender_type,
        body=body,
        twilio_message_sid=message.sid,
    )

    return message.sid


async def save_message(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    business_id: uuid.UUID,
    direction: str,
    sender_type: str,
    body: str,
    twilio_message_sid: str | None = None,
) -> Message:
    """Save a message record to the database."""
    message = Message(
        conversation_id=conversation_id,
        business_id=business_id,
        direction=direction,
        sender_type=sender_type,
        body=body,
        twilio_message_sid=twilio_message_sid,
        status="received" if direction == "inbound" else "sent",
    )
    db.add(message)
    await db.flush()
    return message


async def handle_opt_out(
    db: AsyncSession, phone: str, business_id: uuid.UUID
) -> None:
    """Handle STOP keyword — add to opt-out list, close conversations."""
    # Add opt-out record (ignore if already exists)
    existing = await db.execute(
        select(OptOut.id).where(
            OptOut.phone == phone, OptOut.business_id == business_id
        )
    )
    if not existing.scalar_one_or_none():
        opt_out = OptOut(
            phone=phone, business_id=business_id, reason="stop_keyword"
        )
        db.add(opt_out)

    # Close all active conversations for this phone + business
    lead_ids = select(Lead.id).where(
        Lead.business_id == business_id, Lead.phone == phone
    )
    await db.execute(
        update(Conversation)
        .where(
            Conversation.business_id == business_id,
            Conversation.lead_id.in_(lead_ids),
            Conversation.status.in_(["active", "follow_up", "human_active"]),
        )
        .values(status="closed_opted_out")
    )

    # Update lead status
    await db.execute(
        update(Lead)
        .where(Lead.business_id == business_id, Lead.phone == phone)
        .values(status="opted_out")
    )
    await db.flush()


async def handle_opt_in(
    db: AsyncSession, phone: str, business_id: uuid.UUID
) -> None:
    """Handle START keyword — remove from opt-out list."""
    await db.execute(
        delete(OptOut).where(
            OptOut.phone == phone, OptOut.business_id == business_id
        )
    )
    await db.flush()
