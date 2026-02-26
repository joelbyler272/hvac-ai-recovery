"""
Vapi.ai Voice AI service layer.

Handles:
- Creating/updating Vapi assistants per business
- Building voice AI system prompts
- Transferring missed calls to Vapi
- Processing call results (transcripts, extracted data, recordings)
"""

import logging
import uuid

import httpx
from sqlalchemy import select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.business import Business
from app.models.lead import Lead
from app.models.service import Service
from app.models.voice_ai_config import VoiceAIConfig

logger = logging.getLogger(__name__)
settings = get_settings()

VAPI_API_BASE = "https://api.vapi.ai"


class VapiUnavailableError(Exception):
    """Raised when Vapi API is unreachable or returns an error."""
    pass


def _vapi_headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.vapi_api_key}",
        "Content-Type": "application/json",
    }


def _format_services_for_voice(services: list[Service]) -> str:
    """Format services list for the voice AI prompt."""
    if not services:
        return "General HVAC services (heating, cooling, maintenance)"

    lines = []
    for svc in services:
        if svc.is_bookable and svc.price:
            lines.append(
                f"- {svc.name}: ${svc.price:.0f} (fixed price) — can schedule directly"
            )
        else:
            lines.append(
                f"- {svc.name}: requires on-site estimate — schedule free estimate visit"
            )
    return "\n".join(lines)


def build_voice_system_prompt(
    business: Business,
    services: list[Service] | None = None,
    config: VoiceAIConfig | None = None,
) -> str:
    """Build the system prompt for the Vapi voice AI assistant."""
    if config and config.system_prompt_override:
        return config.system_prompt_override

    services_text = _format_services_for_voice(services or [])

    consent_line = ""
    if business.two_party_consent_state:
        consent_line = (
            "\n\nIMPORTANT: At the very start of the call, briefly say: "
            '"Just so you know, this call may be recorded for quality purposes." '
            "Keep it natural and move on."
        )

    custom_instructions = ""
    if business.ai_instructions:
        custom_instructions = f"\n\nADDITIONAL INSTRUCTIONS FROM BUSINESS OWNER:\n{business.ai_instructions}"

    return f"""You are a friendly, helpful receptionist for {business.name}, an HVAC company.

You are answering a phone call that nobody in the office could pick up. The caller doesn't know you're AI — you're just a helpful team member.

PERSONALITY:
- Warm, friendly, natural. Short sentences, natural pauses.
- Use occasional filler: "sure thing", "absolutely", "let me get that for you"
- If you don't understand, say "Sorry, could you say that one more time?"
- Never sound robotic or scripted
- Mirror the caller's energy

GOALS (in order):
1. Find out what they need
2. Check for emergencies (no heat, gas smell, CO alarm, flooding)
3. Get their name
4. Get the service address
5. Offer to schedule
6. Confirm everything before ending

NEVER DO:
- Say you're AI, virtual assistant, or automated
- Quote specific prices unless it's a fixed-price service listed below
- Diagnose problems (say "sounds like it needs a look")
- Make timing promises you can't keep (say "someone will call to confirm")

EMERGENCY HANDLING:
If gas smell, CO, no heat with vulnerable people, flooding:
- Immediately: "That sounds urgent — let me make sure someone gets to you quickly"
- Get name + address as minimum
- "Someone will call you within a few minutes. If it's a gas smell, please step outside and call 911."

SERVICES & PRICING:
{services_text}
For fixed-price services, you may mention the price.
For everything else: "We'd need to take a look — we can schedule a free estimate."

ENDING THE CALL:
Confirm: "Let me make sure I have everything — [Name], [service] at [address], [time] works for you. Someone will call to confirm. Anything else?"
Then: "Thanks for calling {business.name}! We'll take good care of you."{consent_line}{custom_instructions}"""


# ── Vapi function tools for real-time data extraction during calls ──

VAPI_FUNCTION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "save_lead_info",
            "description": "Save customer information as it is mentioned during the call",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Customer's full name",
                    },
                    "service_needed": {
                        "type": "string",
                        "description": "What HVAC service or problem they described",
                    },
                    "urgency": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "emergency"],
                        "description": "How urgent the request is",
                    },
                    "address": {
                        "type": "string",
                        "description": "Service address",
                    },
                    "preferred_time": {
                        "type": "string",
                        "description": "When they'd like the appointment",
                    },
                    "additional_notes": {
                        "type": "string",
                        "description": "Any other relevant details",
                    },
                },
                "required": [],
            },
        },
        "server": {
            "url": f"{settings.base_url}/webhook/vapi/function-call",
        },
    },
    {
        "type": "function",
        "function": {
            "name": "flag_emergency",
            "description": "Flag this call as an emergency requiring immediate owner attention",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Why this is an emergency (gas leak, no heat, CO, flooding, etc.)",
                    },
                },
                "required": ["reason"],
            },
        },
        "server": {
            "url": f"{settings.base_url}/webhook/vapi/function-call",
        },
    },
    {
        "type": "function",
        "function": {
            "name": "request_human_callback",
            "description": "Request that a human team member calls the customer back for issues AI cannot handle",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Why a human is needed (warranty question, pricing dispute, angry customer, etc.)",
                    },
                },
                "required": ["reason"],
            },
        },
        "server": {
            "url": f"{settings.base_url}/webhook/vapi/function-call",
        },
    },
]


async def create_or_update_assistant(
    db: AsyncSession,
    business: Business,
) -> str:
    """
    Create or update a Vapi assistant for a business.

    Returns the Vapi assistant ID.
    """
    # Load services
    services_result = await db.execute(
        select(Service)
        .where(Service.business_id == business.id, Service.is_active == True)
        .order_by(Service.sort_order)
    )
    services = list(services_result.scalars().all())

    # Load voice AI config if exists
    config_result = await db.execute(
        select(VoiceAIConfig).where(VoiceAIConfig.business_id == business.id)
    )
    config = config_result.scalar_one_or_none()

    system_prompt = build_voice_system_prompt(business, services, config)

    greeting = "Hi! Thanks for calling {}. Sorry nobody could get to the phone — I can help you out though. What's going on?".format(
        business.name
    )
    if config and config.greeting_override:
        greeting = config.greeting_override
    elif business.ai_greeting:
        greeting = business.ai_greeting

    max_duration = 300
    if config:
        max_duration = config.max_call_duration_seconds

    assistant_payload = {
        "name": f"CallHook - {business.name}",
        "model": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
            ],
            "tools": VAPI_FUNCTION_TOOLS,
        },
        "voice": {
            "provider": "11labs",
            "voiceId": config.voice_id if config and config.voice_id else "21m00Tcm4TlvDq8ikWAM",
        },
        "firstMessage": greeting,
        "maxDurationSeconds": max_duration,
        "serverUrl": f"{settings.base_url}/webhook/vapi/call-ended",
        "recordingEnabled": business.call_recording_enabled,
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            if business.vapi_assistant_id:
                # Update existing assistant
                resp = await client.patch(
                    f"{VAPI_API_BASE}/assistant/{business.vapi_assistant_id}",
                    headers=_vapi_headers(),
                    json=assistant_payload,
                )
            else:
                # Create new assistant
                resp = await client.post(
                    f"{VAPI_API_BASE}/assistant",
                    headers=_vapi_headers(),
                    json=assistant_payload,
                )

            if resp.status_code not in (200, 201):
                logger.error(f"Vapi API error: {resp.status_code} {resp.text}")
                raise VapiUnavailableError(f"Vapi returned {resp.status_code}")

            data = resp.json()
            assistant_id = data["id"]

            # Save assistant ID on business
            await db.execute(
                sa_update(Business)
                .where(Business.id == business.id)
                .values(vapi_assistant_id=assistant_id)
            )

            # Create or update voice AI config
            if not config:
                config = VoiceAIConfig(
                    business_id=business.id,
                    provider_assistant_id=assistant_id,
                )
                db.add(config)
            else:
                await db.execute(
                    sa_update(VoiceAIConfig)
                    .where(VoiceAIConfig.business_id == business.id)
                    .values(provider_assistant_id=assistant_id)
                )

            await db.flush()
            return assistant_id

    except httpx.HTTPError as e:
        logger.error(f"Vapi API connection error: {e}")
        raise VapiUnavailableError(str(e)) from e


async def transfer_call_to_vapi(
    business: Business,
    caller_phone: str,
    call_id: uuid.UUID,
) -> str:
    """
    Initiate a Vapi outbound call to the caller, effectively transferring them
    to the voice AI.

    In production with Twilio SIP trunking, this would be a seamless transfer.
    For MVP, we use Vapi's phone call API to call the customer back immediately.

    Returns the Vapi call ID.
    """
    if not business.vapi_assistant_id:
        raise VapiUnavailableError("No Vapi assistant configured for this business")

    if not settings.vapi_api_key:
        raise VapiUnavailableError("VAPI_API_KEY not configured")

    call_payload = {
        "assistantId": business.vapi_assistant_id,
        "customer": {
            "number": caller_phone,
        },
        "phoneNumberId": None,  # Uses Vapi's default number; configure per-business in production
        "metadata": {
            "callhook_call_id": str(call_id),
            "business_id": str(business.id),
        },
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{VAPI_API_BASE}/call/phone",
                headers=_vapi_headers(),
                json=call_payload,
            )

            if resp.status_code not in (200, 201):
                logger.error(f"Vapi call transfer error: {resp.status_code} {resp.text}")
                raise VapiUnavailableError(f"Vapi call API returned {resp.status_code}")

            data = resp.json()
            return data["id"]

    except httpx.HTTPError as e:
        logger.error(f"Vapi call transfer connection error: {e}")
        raise VapiUnavailableError(str(e)) from e


async def get_vapi_assistant_id(
    db: AsyncSession,
    business: Business,
) -> str | None:
    """Get the Vapi assistant ID for a business, creating one if needed."""
    if business.vapi_assistant_id:
        return business.vapi_assistant_id

    # Try to create one on the fly if we have an API key
    if settings.vapi_api_key:
        try:
            return await create_or_update_assistant(db, business)
        except VapiUnavailableError:
            logger.warning(f"Could not auto-create Vapi assistant for business {business.id}")
            return None

    return None
