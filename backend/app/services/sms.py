import uuid

from twilio.rest import Client

from app.config import get_settings

settings = get_settings()
twilio_client = Client(settings.twilio_account_sid, settings.twilio_auth_token)


async def send_sms(
    to: str,
    from_: str,
    body: str,
    conversation_id: uuid.UUID,
    business_id: uuid.UUID,
) -> str:
    """Send an SMS via Twilio and save to database."""
    message = twilio_client.messages.create(
        to=to,
        from_=from_,
        body=body,
        status_callback=f"{settings.base_url}/webhook/sms/status",
    )

    await save_message(
        conversation_id=conversation_id,
        business_id=business_id,
        direction="outbound",
        sender_type="ai",
        body=body,
        twilio_message_sid=message.sid,
    )

    return message.sid


async def save_message(
    conversation_id: uuid.UUID,
    business_id: uuid.UUID,
    direction: str,
    sender_type: str,
    body: str,
    twilio_message_sid: str | None = None,
) -> None:
    """Save a message record to the database."""
    # TODO: Implement DB save
    pass


async def handle_opt_out(phone: str, business_id: uuid.UUID) -> None:
    """Handle STOP keyword — add to opt-out list, close conversations."""
    # TODO: Implement opt-out handling
    pass


async def handle_opt_in(phone: str, business_id: uuid.UUID) -> None:
    """Handle START keyword — remove from opt-out list."""
    # TODO: Implement opt-in handling
    pass
