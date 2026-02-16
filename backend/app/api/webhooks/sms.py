from fastapi import APIRouter, Request
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse

from app.services.voice import (
    get_business_by_twilio_number,
    get_active_conversation,
    create_or_get_lead,
    create_conversation,
)
from app.services.sms import send_sms, save_message, handle_opt_out, handle_opt_in
from app.services.ai_engine import generate_ai_response
from app.services.notifications import notify_owner
from app.services.follow_up import cancel_pending_follow_ups, schedule_follow_up

router = APIRouter()


@router.post("/incoming")
async def sms_incoming(request: Request):
    """
    Handles all incoming SMS messages.
    Matches to existing conversation or creates new one.
    """
    form = await request.form()
    from_number = form.get("From")
    to_number = form.get("To")
    body = form.get("Body", "").strip()

    business = await get_business_by_twilio_number(to_number)
    if not business:
        return Response(status_code=200)

    # TCPA Compliance: Check for opt-out keywords
    if body.upper() in ["STOP", "UNSUBSCRIBE", "CANCEL", "END", "QUIT"]:
        await handle_opt_out(from_number, business.id)
        response = MessagingResponse()
        response.message(
            f"You've been unsubscribed from {business.name} messages. "
            f"Reply START to re-subscribe."
        )
        return Response(content=str(response), media_type="application/xml")

    if body.upper() in ["START", "YES", "UNSTOP"]:
        await handle_opt_in(from_number, business.id)
        response = MessagingResponse()
        response.message(
            f"Welcome back! You'll now receive messages from {business.name}."
        )
        return Response(content=str(response), media_type="application/xml")

    # Find active conversation
    conversation = await get_active_conversation(
        business_id=business.id, phone=from_number
    )

    if not conversation:
        lead = await create_or_get_lead(
            business_id=business.id,
            phone=from_number,
            source="manual",
        )
        conversation = await create_conversation(
            business_id=business.id, lead_id=lead.id
        )

    # Save inbound message
    await save_message(
        conversation_id=conversation.id,
        business_id=business.id,
        direction="inbound",
        sender_type="caller",
        body=body,
        twilio_message_sid=form.get("MessageSid"),
    )

    # Cancel any pending follow-ups
    await cancel_pending_follow_ups(conversation.id)

    # If human has taken over, just notify
    if conversation.status == "human_active":
        await notify_owner(
            business=business,
            event="new_message",
            data={"from": from_number, "body": body},
        )
        return Response(status_code=200)

    # AI Response
    ai_response = await generate_ai_response(
        conversation=conversation,
        business=business,
        new_message=body,
    )

    await send_sms(
        to=from_number,
        from_=business.twilio_number,
        body=ai_response,
        conversation_id=conversation.id,
        business_id=business.id,
    )

    # Schedule follow-up if no reply in 2 hours
    await schedule_follow_up(
        conversation_id=conversation.id, delay_minutes=120
    )

    return Response(status_code=200)


@router.post("/status")
async def sms_status(request: Request):
    """Twilio SMS delivery status callback."""
    # TODO: Update message delivery status
    return Response(status_code=200)
