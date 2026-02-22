import json
import logging
from datetime import datetime

import pytz
from openai import AsyncOpenAI
from sqlalchemy import select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.business import Business
from app.models.conversation import Conversation
from app.models.lead import Lead
from app.models.message import Message
from app.models.service import Service

logger = logging.getLogger(__name__)
settings = get_settings()

_openai_client = None


def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _openai_client


def _format_services_for_prompt(services: list[Service]) -> str:
    """Format services with pricing for the AI prompt."""
    if not services:
        return "HVAC Services (general)"

    lines = []
    for svc in services:
        if svc.is_bookable and svc.price:
            lines.append(
                f"- {svc.name}: ${svc.price:.0f} (fixed price, ~{svc.duration_minutes} min) — Can book directly"
            )
        else:
            lines.append(
                f"- {svc.name}: Requires on-site estimate visit (~{svc.duration_minutes} min)"
            )
    return "\n".join(lines)


def build_system_prompt(
    business: Business,
    lead: Lead,
    conversation: Conversation,
    services: list[Service] | None = None,
) -> str:
    """Build the system prompt for the AI conversation."""
    current_time = datetime.now(pytz.timezone(business.timezone))
    is_business_hrs = check_business_hours(business, current_time)
    day_of_week = current_time.strftime("%A")

    services_text = _format_services_for_prompt(services or [])

    return f"""You are a helpful, friendly assistant for {business.name}, an HVAC company.

CRITICAL RULES:
- You are NOT an AI chatbot. You are a helpful team member at {business.name}.
- Never say you are an AI, a bot, a virtual assistant, or automated.
- Keep messages SHORT. 1-3 sentences max. These are SMS texts, not emails.
- Be warm, professional, and conversational.
- Use the customer's name once you learn it.
- Never make up information.
- Never diagnose problems.

YOUR JOB:
You're following up after a missed call. Your goal is to:
1. Find out what they need (what HVAC service/problem)
2. Understand urgency (emergency vs can wait)
3. Get their name
4. Get the service address
5. Offer to schedule an appointment

QUALIFICATION FLOW (gather naturally):
1. Service needed
2. Urgency
3. Name
4. Address
5. Preferred time

BUSINESS INFORMATION:
- Company: {business.name}
- Business hours: {json.dumps(business.business_hours)}
- Current time: {current_time.strftime('%I:%M %p')} on {day_of_week}
- Currently: {"within business hours" if is_business_hrs else "after hours"}

SERVICES & PRICING:
{services_text}

SERVICE BOOKING RULES:
- For services marked "Can book directly" (fixed price): You may tell the customer the price and offer to schedule the service directly.
- For services marked "Requires on-site estimate": Do NOT quote a price. Tell the customer we need to take a look first, and offer to schedule a free estimate visit.
- If the customer asks about price for an estimate-required service, say something like "That depends on a few factors — we'd need to take a look first. We can schedule a free estimate visit for you."

{f"ADDITIONAL INSTRUCTIONS: {business.ai_instructions}" if business.ai_instructions else ""}

WHAT WE KNOW SO FAR:
- Name: {lead.name or "Unknown"}
- Service needed: {lead.service_needed or "Unknown"}
- Urgency: {lead.urgency or "Unknown"}
- Address: {lead.address or "Unknown"}

SIGNALS:
- When lead is qualified (have service, name, address, preferred time): end with [QUALIFIED]
- If caller is upset or has complex issue: end with [HUMAN_NEEDED]
- If emergency (no heat in winter, gas smell, flooding, CO detector): end with [EMERGENCY]

STYLE:
- Match the customer's energy
- Don't ask more than one question at a time
- Use everyday language
"""


def check_business_hours(business: Business, current_time: datetime) -> bool:
    """Check if the current time is within business hours."""
    day = current_time.strftime("%A").lower()
    hours = business.business_hours.get(day)

    if not hours:
        return False

    open_time = datetime.strptime(hours["open"], "%H:%M").time()
    close_time = datetime.strptime(hours["close"], "%H:%M").time()
    return open_time <= current_time.time() <= close_time


async def generate_ai_response(
    db: AsyncSession,
    conversation: Conversation,
    business: Business,
    new_message: str,
) -> str:
    """Generate an AI response using OpenAI."""
    # Load lead from DB
    lead_result = await db.execute(
        select(Lead).where(Lead.id == conversation.lead_id)
    )
    lead = lead_result.scalar_one_or_none() or Lead()

    # Load active services for the business
    services_result = await db.execute(
        select(Service)
        .where(Service.business_id == business.id, Service.is_active == True)
        .order_by(Service.sort_order)
    )
    services = list(services_result.scalars().all())

    # Load conversation history
    msg_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.asc())
    )
    messages = msg_result.scalars().all()

    openai_messages = [
        {"role": "system", "content": build_system_prompt(business, lead, conversation, services)}
    ]

    for msg in messages:
        role = "assistant" if msg.sender_type == "ai" else "user"
        openai_messages.append({"role": role, "content": msg.body})

    # Add the new incoming message
    openai_messages.append({"role": "user", "content": new_message})

    # Update lead status progression
    if lead.status == "new":
        await db.execute(
            sa_update(Lead).where(Lead.id == lead.id).values(status="contacted")
        )

    client = _get_openai_client()
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=openai_messages,
        max_tokens=200,
        temperature=0.7,
    )

    ai_text = response.choices[0].message.content.strip()

    # Check for qualification signals
    if "[QUALIFIED]" in ai_text:
        ai_text = ai_text.replace("[QUALIFIED]", "").strip()
        await _handle_qualified_lead(db, conversation, lead, business)

    if "[HUMAN_NEEDED]" in ai_text:
        ai_text = ai_text.replace("[HUMAN_NEEDED]", "").strip()
        await _handle_human_needed(db, conversation, business)

    if "[EMERGENCY]" in ai_text:
        ai_text = ai_text.replace("[EMERGENCY]", "").strip()
        await _handle_emergency(db, conversation, lead, business)

    # Extract qualification data via function calling
    await _extract_qualification_data(db, lead, new_message)

    return ai_text


async def _match_service(
    db: AsyncSession, business_id, service_text: str | None
) -> Service | None:
    """Fuzzy-match service_text to an active Service record."""
    if not service_text:
        return None
    service_text_lower = service_text.lower()
    result = await db.execute(
        select(Service).where(
            Service.business_id == business_id,
            Service.is_active == True,
        )
    )
    services = result.scalars().all()
    for svc in services:
        if svc.name.lower() in service_text_lower or service_text_lower in svc.name.lower():
            return svc
    return None


async def _handle_qualified_lead(
    db: AsyncSession,
    conversation: Conversation,
    lead: Lead,
    business: Business,
) -> None:
    """Handle a qualified lead signal."""
    # Try to match the service for accurate pricing
    matched_service = await _match_service(db, business.id, lead.service_needed)
    estimated_value = (
        float(matched_service.price)
        if matched_service and matched_service.price
        else float(business.avg_job_value or 350)
    )

    await db.execute(
        sa_update(Lead)
        .where(Lead.id == lead.id)
        .values(
            status="qualified",
            estimated_value=estimated_value,
        )
    )
    await db.execute(
        sa_update(Conversation)
        .where(Conversation.id == conversation.id)
        .values(status="qualified")
    )

    from app.services.notifications import notify_owner

    await notify_owner(
        business=business,
        event="qualified_lead",
        data={"lead": lead},
    )


async def _handle_human_needed(
    db: AsyncSession,
    conversation: Conversation,
    business: Business,
) -> None:
    """Handle a human-needed signal."""
    await db.execute(
        sa_update(Conversation)
        .where(Conversation.id == conversation.id)
        .values(status="human_active")
    )

    from app.services.notifications import notify_owner

    await notify_owner(
        business=business,
        event="human_needed",
        data={},
    )


async def _handle_emergency(
    db: AsyncSession,
    conversation: Conversation,
    lead: Lead,
    business: Business,
) -> None:
    """Handle an emergency signal."""
    await db.execute(
        sa_update(Lead)
        .where(Lead.id == lead.id)
        .values(urgency="emergency")
    )
    await db.execute(
        sa_update(Conversation)
        .where(Conversation.id == conversation.id)
        .values(status="human_active")
    )

    from app.services.notifications import notify_owner

    await notify_owner(
        business=business,
        event="emergency",
        data={"lead": lead},
    )


EXTRACTION_FUNCTIONS = [
    {
        "name": "update_lead_info",
        "description": "Extract customer information mentioned in the message",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Customer's name if mentioned",
                },
                "service_needed": {
                    "type": "string",
                    "description": "HVAC service or problem described",
                },
                "urgency": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "emergency"],
                    "description": "How urgent the request is",
                },
                "address": {
                    "type": "string",
                    "description": "Service address if mentioned",
                },
                "preferred_time": {
                    "type": "string",
                    "description": "Preferred appointment time if mentioned",
                },
            },
            "required": [],
        },
    }
]


async def _extract_qualification_data(
    db: AsyncSession,
    lead: Lead,
    customer_message: str,
) -> None:
    """Use function calling to extract lead qualification data from messages."""
    # Skip if already fully qualified
    if lead.name and lead.service_needed and lead.address:
        return

    try:
        client = _get_openai_client()
        extraction = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Extract any customer information from this message. Only extract what is explicitly stated.",
                },
                {"role": "user", "content": customer_message},
            ],
            tools=[{"type": "function", "function": f} for f in EXTRACTION_FUNCTIONS],
            tool_choice="auto",
            max_tokens=150,
        )

        if extraction.choices[0].message.tool_calls:
            tool_call = extraction.choices[0].message.tool_calls[0]
            data = json.loads(tool_call.function.arguments)

            update_vals = {}
            if data.get("name") and not lead.name:
                update_vals["name"] = data["name"]
            if data.get("service_needed") and not lead.service_needed:
                update_vals["service_needed"] = data["service_needed"]
            if data.get("urgency") and not lead.urgency:
                update_vals["urgency"] = data["urgency"]
            if data.get("address") and not lead.address:
                update_vals["address"] = data["address"]
            if data.get("preferred_time") and not lead.preferred_time:
                update_vals["preferred_time"] = data["preferred_time"]

            if update_vals:
                # Progress lead status
                if lead.status == "contacted":
                    update_vals["status"] = "qualifying"

                await db.execute(
                    sa_update(Lead).where(Lead.id == lead.id).values(**update_vals)
                )
    except Exception as e:
        logger.warning(f"Failed to extract qualification data: {e}")
