import logging

from fastapi import APIRouter, Request, Depends
from fastapi.responses import Response
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession
from twilio.twiml.voice_response import VoiceResponse

from app.config import get_settings
from app.database import get_db
from app.services.voice import (
    get_business_by_twilio_number,
    create_call_record,
    is_after_hours,
    get_call,
    update_call,
    is_opted_out,
    get_active_conversation,
    create_or_get_lead,
    create_conversation,
)
from app.services.sms import send_sms
from app.services.notifications import notify_owner
from app.services.follow_up import schedule_follow_up
from app.services.lookup import detect_line_type, can_receive_sms
from app.services.vapi import transfer_call_to_vapi, VapiUnavailableError
from app.models.call import Call
from app.models.conversation import Conversation

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


@router.post("/incoming")
async def voice_incoming(request: Request, db: AsyncSession = Depends(get_db)):
    """Twilio sends this when a call comes in."""
    form = await request.form()
    from_number = form.get("From")
    to_number = form.get("To")

    business = await get_business_by_twilio_number(db, to_number)

    if not business:
        response = VoiceResponse()
        response.say("Sorry, this number is not configured.")
        return Response(content=str(response), media_type="application/xml")

    call = await create_call_record(
        db,
        business_id=business.id,
        twilio_call_sid=form.get("CallSid"),
        caller_phone=from_number,
        status="ringing",
        is_after_hours=is_after_hours(business),
    )

    response = VoiceResponse()
    dial = response.dial(
        timeout=20,
        action=f"{settings.base_url}/webhook/voice/call-completed?call_id={call.id}",
        method="POST",
        caller_id=to_number,
    )
    dial.number(
        business.business_phone,
        status_callback=f"{settings.base_url}/webhook/voice/dial-status",
        status_callback_event="initiated ringing answered completed",
    )

    return Response(content=str(response), media_type="application/xml")


@router.post("/call-completed")
async def call_completed(
    request: Request, call_id: str, db: AsyncSession = Depends(get_db)
):
    """
    Fires after Dial completes. Detects missed calls and routes to voice AI.

    Flow for missed calls:
    1. Detect line type (mobile/landline/voip)
    2. Create lead + conversation
    3. Transfer call to Vapi voice AI
    4. If Vapi is unavailable, fall back to SMS text-back
    """
    form = await request.form()
    dial_status = form.get("DialCallStatus")
    caller_phone = form.get("From")

    call = await get_call(db, call_id)
    business = await get_business_by_twilio_number(db, form.get("To"))

    if not business or not call:
        response = VoiceResponse()
        return Response(content=str(response), media_type="application/xml")

    # === CALL ANSWERED ===
    if dial_status == "completed":
        await update_call(
            db,
            call.id,
            status="answered",
            duration=int(form.get("DialCallDuration", 0)),
        )
        response = VoiceResponse()
        return Response(content=str(response), media_type="application/xml")

    # === MISSED CALL ===
    await update_call(db, call.id, status="missed")

    # Check if caller has opted out
    if await is_opted_out(db, caller_phone, business.id):
        response = VoiceResponse()
        response.say("Sorry we missed your call. Please try again later.")
        return Response(content=str(response), media_type="application/xml")

    # Detect line type (mobile, landline, voip)
    line_type = await detect_line_type(caller_phone)
    await db.execute(
        sa_update(Call).where(Call.id == call.id).values(line_type=line_type)
    )

    # Check for existing active conversation
    existing_convo = await get_active_conversation(
        db, business_id=business.id, phone=caller_phone
    )

    if not existing_convo:
        lead = await create_or_get_lead(
            db, business_id=business.id, phone=caller_phone, source="missed_call"
        )

        conversation = await create_conversation(
            db,
            business_id=business.id,
            lead_id=lead.id,
            call_id=call.id,
            channel="voice",
        )
    else:
        conversation = existing_convo

    # === TRY VOICE AI (PRIMARY) ===
    if settings.vapi_api_key and business.vapi_assistant_id:
        try:
            vapi_call_id = await transfer_call_to_vapi(
                business=business,
                caller_phone=caller_phone,
                call_id=call.id,
            )

            # Update call with Vapi ID
            await db.execute(
                sa_update(Call)
                .where(Call.id == call.id)
                .values(vapi_call_id=vapi_call_id, voice_ai_used=True)
            )

            # Notify owner that AI is answering
            await notify_owner(
                business=business,
                event="missed_call",
                data={
                    "caller_phone": caller_phone,
                    "after_hours": call.is_after_hours,
                    "voice_ai": True,
                },
            )

            # Return TwiML — the caller hears a brief message while Vapi calls them back
            response = VoiceResponse()
            response.say(
                f"Thanks for calling {business.name}. "
                f"One moment while I connect you with our team."
            )
            response.pause(length=2)
            response.say("You'll receive a call right back. Thank you!")
            return Response(content=str(response), media_type="application/xml")

        except VapiUnavailableError as e:
            logger.error(f"Vapi unavailable, falling back to SMS: {e}")
            # Fall through to SMS fallback below

    # === SMS FALLBACK ===
    await _sms_fallback(
        db=db,
        call=call,
        business=business,
        caller_phone=caller_phone,
        conversation=conversation,
        line_type=line_type,
    )

    response = VoiceResponse()
    if can_receive_sms(line_type):
        response.say(
            f"Sorry we can't take your call right now. "
            f"We'll text you right away to help. Thanks for calling {business.name}!"
        )
    else:
        response.say(
            f"Sorry we can't take your call right now. "
            f"Someone from {business.name} will call you back shortly. Thank you!"
        )
    return Response(content=str(response), media_type="application/xml")


async def _sms_fallback(
    db: AsyncSession,
    call: Call,
    business,
    caller_phone: str,
    conversation: Conversation,
    line_type: str,
) -> None:
    """
    Fall back to SMS text-back when voice AI is unavailable.

    For mobile callers: sends greeting SMS + schedules follow-up.
    For landline callers: notifies owner for manual callback.
    """
    if can_receive_sms(line_type):
        greeting = business.ai_greeting or (
            f"Hey! Sorry we missed your call. This is {business.name}. "
            f"How can we help you today?"
        )

        await send_sms(
            db,
            to=caller_phone,
            from_=business.twilio_number,
            body=greeting,
            conversation_id=conversation.id,
            business_id=business.id,
        )

        await schedule_follow_up(
            conversation_id=conversation.id, delay_minutes=120
        )

    # Always notify owner
    await notify_owner(
        business=business,
        event="missed_call",
        data={
            "caller_phone": caller_phone,
            "after_hours": call.is_after_hours,
            "voice_ai": False,
            "line_type": line_type,
        },
    )

    # For landline callers who can't receive SMS, flag for manual callback
    if not can_receive_sms(line_type):
        await notify_owner(
            business=business,
            event="human_needed",
            data={
                "reason": "Landline caller — cannot send SMS, voice AI unavailable",
                "caller_phone": caller_phone,
            },
        )


@router.post("/dial-status")
async def dial_status(request: Request):
    """Receives dial status callbacks (for logging)."""
    return Response(status_code=200)
