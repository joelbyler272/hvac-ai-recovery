from fastapi import APIRouter, Request, Depends
from fastapi.responses import Response
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
    """Fires after Dial completes. Detects missed calls and triggers SMS flow."""
    form = await request.form()
    dial_status = form.get("DialCallStatus")
    caller_phone = form.get("From")

    call = await get_call(db, call_id)
    business = await get_business_by_twilio_number(db, form.get("To"))

    if not business or not call:
        response = VoiceResponse()
        return Response(content=str(response), media_type="application/xml")

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

    if await is_opted_out(db, caller_phone, business.id):
        response = VoiceResponse()
        response.say("Sorry we missed your call. Please try again later.")
        return Response(content=str(response), media_type="application/xml")

    existing_convo = await get_active_conversation(
        db, business_id=business.id, phone=caller_phone
    )

    if not existing_convo:
        lead = await create_or_get_lead(
            db, business_id=business.id, phone=caller_phone, source="missed_call"
        )

        conversation = await create_conversation(
            db, business_id=business.id, lead_id=lead.id, call_id=call.id
        )

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

        await notify_owner(
            business=business,
            event="missed_call",
            data={
                "caller_phone": caller_phone,
                "after_hours": call.is_after_hours,
            },
        )

    response = VoiceResponse()
    response.say(
        f"Sorry we can't take your call right now. "
        f"We'll text you right away to help. Thanks for calling {business.name}!"
    )
    return Response(content=str(response), media_type="application/xml")


@router.post("/dial-status")
async def dial_status(request: Request):
    """Receives dial status callbacks (for logging)."""
    return Response(status_code=200)
