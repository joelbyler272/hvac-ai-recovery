"""
Vapi.ai webhook handlers.

Two endpoints:
1. /webhook/vapi/call-ended — receives end-of-call data (transcript, extracted info, recording)
2. /webhook/vapi/function-call — receives real-time function calls during active calls
"""

import logging
import uuid

from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.business import Business
from app.models.call import Call
from app.models.conversation import Conversation
from app.models.lead import Lead
from app.services.notifications import notify_owner
from app.services.lookup import can_receive_sms

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/call-ended")
async def vapi_call_ended(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Vapi sends this when a voice AI call ends.

    Payload includes: transcript, extracted data, duration, recording URL, cost.
    We use this to:
    - Update call record with voice AI details
    - Update lead with extracted qualification data
    - Save transcript to conversation
    - Trigger owner notification
    - Send confirmation SMS to mobile callers
    - Schedule follow-up if qualification was incomplete
    """
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    message_type = payload.get("message", {}).get("type", "")

    # Vapi sends various message types; we care about "end-of-call-report"
    if message_type != "end-of-call-report":
        # Acknowledge other message types (status-update, transcript, etc.)
        return JSONResponse({"ok": True})

    message = payload.get("message", {})
    call_data = message.get("call", {})
    vapi_call_id = call_data.get("id")
    metadata = call_data.get("metadata", {})
    callhook_call_id = metadata.get("callhook_call_id")
    business_id = metadata.get("business_id")

    if not callhook_call_id or not business_id:
        logger.warning("Vapi call-ended webhook missing callhook metadata")
        return JSONResponse({"ok": True})

    # Load call and business
    call_result = await db.execute(
        select(Call).where(Call.id == uuid.UUID(callhook_call_id))
    )
    call = call_result.scalar_one_or_none()

    business_result = await db.execute(
        select(Business).where(Business.id == uuid.UUID(business_id))
    )
    business = business_result.scalar_one_or_none()

    if not call or not business:
        logger.warning(f"Vapi call-ended: call or business not found (call={callhook_call_id})")
        return JSONResponse({"ok": True})

    # Extract data from Vapi payload
    transcript_parts = message.get("transcript", "")
    if isinstance(transcript_parts, list):
        transcript_text = "\n".join(
            f"{t.get('role', 'unknown')}: {t.get('content', '')}"
            for t in transcript_parts
        )
    else:
        transcript_text = str(transcript_parts)

    duration_seconds = int(call_data.get("duration", 0) or 0)
    recording_url = message.get("recordingUrl") or call_data.get("recordingUrl")
    cost = message.get("cost") or call_data.get("cost")
    ended_reason = message.get("endedReason", "")

    # Update call record with voice AI data
    call_updates = {
        "voice_ai_used": True,
        "voice_ai_transcript": transcript_text,
        "voice_ai_duration_seconds": duration_seconds,
        "vapi_call_id": vapi_call_id,
    }
    if recording_url:
        call_updates["recording_url"] = recording_url
    if cost is not None:
        call_updates["voice_ai_cost"] = float(cost)
    if duration_seconds > 0:
        call_updates["duration_seconds"] = duration_seconds

    await db.execute(
        sa_update(Call).where(Call.id == call.id).values(**call_updates)
    )

    # Find conversation linked to this call
    convo_result = await db.execute(
        select(Conversation).where(Conversation.call_id == call.id)
    )
    conversation = convo_result.scalar_one_or_none()

    if conversation:
        # Save transcript to conversation
        await db.execute(
            sa_update(Conversation)
            .where(Conversation.id == conversation.id)
            .values(voice_transcript=transcript_text)
        )

        # Load lead
        lead_result = await db.execute(
            select(Lead).where(Lead.id == conversation.lead_id)
        )
        lead = lead_result.scalar_one_or_none()

        if lead:
            # Extract structured data from the analysis/summary if available
            analysis = message.get("analysis", {})
            structured_data = analysis.get("structuredData", {})

            lead_updates = {}
            if structured_data.get("name") and not lead.name:
                lead_updates["name"] = structured_data["name"]
            if structured_data.get("service_needed") and not lead.service_needed:
                lead_updates["service_needed"] = structured_data["service_needed"]
            if structured_data.get("urgency") and not lead.urgency:
                lead_updates["urgency"] = structured_data["urgency"]
            if structured_data.get("address") and not lead.address:
                lead_updates["address"] = structured_data["address"]
            if structured_data.get("preferred_time") and not lead.preferred_time:
                lead_updates["preferred_time"] = structured_data["preferred_time"]

            # Determine qualification status
            is_qualified = bool(
                (lead.name or lead_updates.get("name"))
                and (lead.service_needed or lead_updates.get("service_needed"))
                and (lead.address or lead_updates.get("address"))
            )

            if is_qualified and lead.status not in ("qualified", "booked"):
                lead_updates["status"] = "qualified"
                # Estimate value
                from app.services.ai_engine import _match_service
                matched = await _match_service(
                    db, business.id,
                    lead_updates.get("service_needed") or lead.service_needed,
                )
                if matched and matched.price:
                    lead_updates["estimated_value"] = float(matched.price)
                else:
                    lead_updates["estimated_value"] = float(business.avg_job_value or 350)
            elif not is_qualified and lead.status == "new":
                lead_updates["status"] = "qualifying"

            if lead_updates:
                await db.execute(
                    sa_update(Lead).where(Lead.id == lead.id).values(**lead_updates)
                )

            # Update conversation status
            if is_qualified:
                await db.execute(
                    sa_update(Conversation)
                    .where(Conversation.id == conversation.id)
                    .values(status="qualified")
                )

            # Notify business owner
            await notify_owner(
                business=business,
                event="emergency" if lead.urgency == "emergency" else "qualified_lead" if is_qualified else "missed_call",
                data={
                    "lead": lead,
                    "caller_phone": call.caller_phone,
                    "after_hours": call.is_after_hours,
                    "voice_ai": True,
                    "duration": duration_seconds,
                },
            )

            # Send confirmation SMS if caller has a mobile number
            if can_receive_sms(call.line_type) and is_qualified:
                try:
                    from app.services.sms import send_sms

                    caller_name = lead_updates.get("name") or lead.name or ""
                    svc = lead_updates.get("service_needed") or lead.service_needed or "your service"
                    addr = lead_updates.get("address") or lead.address or ""

                    confirmation = (
                        f"Thanks for calling {business.name}"
                        f"{', ' + caller_name if caller_name else ''}! "
                        f"Confirming: {svc}"
                        f"{' at ' + addr if addr else ''}. "
                        f"Someone will call to confirm the time. "
                        f"Text this number anytime if you need anything!"
                    )

                    await send_sms(
                        db,
                        to=call.caller_phone,
                        from_=business.twilio_number,
                        body=confirmation,
                        conversation_id=conversation.id,
                        business_id=business.id,
                        sender_type="ai",
                    )
                except Exception as e:
                    logger.warning(f"Failed to send post-call confirmation SMS: {e}")

            # Schedule SMS follow-up if call was incomplete (caller hung up early)
            if not is_qualified and can_receive_sms(call.line_type):
                try:
                    from app.services.sms import send_sms
                    from app.services.follow_up import schedule_follow_up

                    recovery_msg = (
                        f"Hey! This is {business.name}. "
                        f"Looks like we got disconnected. "
                        f"What time works best to get you scheduled?"
                    )
                    await send_sms(
                        db,
                        to=call.caller_phone,
                        from_=business.twilio_number,
                        body=recovery_msg,
                        conversation_id=conversation.id,
                        business_id=business.id,
                        sender_type="ai",
                    )
                    await schedule_follow_up(
                        conversation_id=conversation.id, delay_minutes=120
                    )
                except Exception as e:
                    logger.warning(f"Failed to send incomplete call recovery SMS: {e}")

            # If landline and incomplete, notify owner for manual callback
            if not is_qualified and not can_receive_sms(call.line_type):
                await notify_owner(
                    business=business,
                    event="human_needed",
                    data={
                        "reason": "Landline caller — call incomplete, cannot send SMS follow-up",
                        "caller_phone": call.caller_phone,
                        "lead": lead,
                    },
                )

            # Schedule owner nudge for qualified leads
            if is_qualified:
                try:
                    from app.worker.tasks import celery_app
                    from app.config import get_settings

                    nudge_delay = get_settings().owner_nudge_delay_minutes
                    celery_app.send_task(
                        "send_owner_nudge",
                        args=[str(business.id), str(lead.id)],
                        countdown=nudge_delay * 60,
                    )
                except Exception as e:
                    logger.warning(f"Failed to schedule owner nudge: {e}")

    await db.flush()
    return JSONResponse({"ok": True})


@router.post("/function-call")
async def vapi_function_call(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Vapi sends this in real-time during active calls when the AI invokes a function tool.

    Functions:
    - save_lead_info: updates lead record with extracted data
    - flag_emergency: triggers immediate owner notification
    - request_human_callback: flags conversation for human follow-up
    """
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    message = payload.get("message", {})
    message_type = message.get("type", "")

    if message_type != "function-call":
        return JSONResponse({"result": "ok"})

    function_call = message.get("functionCall", {})
    fn_name = function_call.get("name", "")
    fn_params = function_call.get("parameters", {})

    call_data = message.get("call", {})
    metadata = call_data.get("metadata", {})
    callhook_call_id = metadata.get("callhook_call_id")
    business_id_str = metadata.get("business_id")

    if not callhook_call_id or not business_id_str:
        return JSONResponse({"result": "Missing metadata"})

    # Load business
    business_result = await db.execute(
        select(Business).where(Business.id == uuid.UUID(business_id_str))
    )
    business = business_result.scalar_one_or_none()

    # Load call and find conversation/lead
    call_result = await db.execute(
        select(Call).where(Call.id == uuid.UUID(callhook_call_id))
    )
    call = call_result.scalar_one_or_none()

    if not business or not call:
        return JSONResponse({"result": "Not found"})

    convo_result = await db.execute(
        select(Conversation).where(Conversation.call_id == call.id)
    )
    conversation = convo_result.scalar_one_or_none()

    lead = None
    if conversation:
        lead_result = await db.execute(
            select(Lead).where(Lead.id == conversation.lead_id)
        )
        lead = lead_result.scalar_one_or_none()

    # ── Handle each function ──

    if fn_name == "save_lead_info" and lead:
        updates = {}
        if fn_params.get("name") and not lead.name:
            updates["name"] = fn_params["name"]
        if fn_params.get("service_needed") and not lead.service_needed:
            updates["service_needed"] = fn_params["service_needed"]
        if fn_params.get("urgency"):
            updates["urgency"] = fn_params["urgency"]
        if fn_params.get("address") and not lead.address:
            updates["address"] = fn_params["address"]
        if fn_params.get("preferred_time"):
            updates["preferred_time"] = fn_params["preferred_time"]
        if fn_params.get("additional_notes"):
            current_notes = lead.notes or ""
            updates["notes"] = (
                f"{current_notes}\n{fn_params['additional_notes']}"
                if current_notes
                else fn_params["additional_notes"]
            )

        if updates:
            if lead.status in ("new", "contacted"):
                updates["status"] = "qualifying"
            await db.execute(
                sa_update(Lead).where(Lead.id == lead.id).values(**updates)
            )
            await db.flush()

        return JSONResponse({"result": "Lead info saved"})

    elif fn_name == "flag_emergency" and lead:
        reason = fn_params.get("reason", "Emergency detected during voice call")

        await db.execute(
            sa_update(Lead).where(Lead.id == lead.id).values(urgency="emergency")
        )
        if conversation:
            await db.execute(
                sa_update(Conversation)
                .where(Conversation.id == conversation.id)
                .values(status="human_active")
            )
        await db.flush()

        await notify_owner(
            business=business,
            event="emergency",
            data={
                "lead": lead,
                "reason": reason,
                "caller_phone": call.caller_phone,
                "voice_ai": True,
            },
        )

        return JSONResponse({"result": "Emergency flagged — owner notified"})

    elif fn_name == "request_human_callback":
        reason = fn_params.get("reason", "Human callback requested during voice call")

        if conversation:
            await db.execute(
                sa_update(Conversation)
                .where(Conversation.id == conversation.id)
                .values(status="human_active")
            )
            await db.flush()

        await notify_owner(
            business=business,
            event="human_needed",
            data={
                "reason": reason,
                "caller_phone": call.caller_phone,
                "lead": lead,
                "voice_ai": True,
            },
        )

        return JSONResponse({"result": "Human callback requested — owner notified"})

    return JSONResponse({"result": f"Unknown function: {fn_name}"})
