import json
from datetime import datetime

import pytz
from openai import AsyncOpenAI

from app.config import get_settings
from app.models.business import Business
from app.models.conversation import Conversation
from app.models.lead import Lead

settings = get_settings()
openai_client = AsyncOpenAI(api_key=settings.openai_api_key)


def build_system_prompt(business: Business, lead: Lead, conversation: Conversation) -> str:
    """Build the system prompt for the AI conversation."""
    current_time = datetime.now(pytz.timezone(business.timezone))
    is_business_hours = check_business_hours(business, current_time)
    day_of_week = current_time.strftime("%A")

    return f"""You are a helpful, friendly assistant for {business.name}, an HVAC company.

CRITICAL RULES:
- You are NOT an AI chatbot. You are a helpful team member at {business.name}.
- Never say you are an AI, a bot, a virtual assistant, or automated.
- Keep messages SHORT. 1-3 sentences max. These are SMS texts, not emails.
- Be warm, professional, and conversational.
- Use the customer's name once you learn it.
- Never make up information.
- Never discuss pricing, give estimates, or promise specific costs.
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
- Services offered: {', '.join(business.services) if business.services else 'HVAC Services'}
- Business hours: {json.dumps(business.business_hours)}
- Current time: {current_time.strftime('%I:%M %p')} on {day_of_week}
- Currently: {"within business hours" if is_business_hours else "after hours"}

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
    conversation: Conversation,
    business: Business,
    new_message: str,
) -> str:
    """Generate an AI response using OpenAI."""
    # TODO: Get full conversation history from DB
    lead = Lead()  # TODO: fetch from DB using conversation.lead_id

    openai_messages = [
        {"role": "system", "content": build_system_prompt(business, lead, conversation)}
    ]

    # TODO: Load conversation history and append messages
    openai_messages.append({"role": "user", "content": new_message})

    response = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=openai_messages,
        max_tokens=200,
        temperature=0.7,
    )

    ai_text = response.choices[0].message.content.strip()

    # Check for qualification signals
    if "[QUALIFIED]" in ai_text:
        ai_text = ai_text.replace("[QUALIFIED]", "").strip()
        # TODO: await handle_qualified_lead(conversation, lead, business)

    if "[HUMAN_NEEDED]" in ai_text:
        ai_text = ai_text.replace("[HUMAN_NEEDED]", "").strip()
        # TODO: await request_human_takeover(conversation, business)

    if "[EMERGENCY]" in ai_text:
        ai_text = ai_text.replace("[EMERGENCY]", "").strip()
        # TODO: await handle_emergency(conversation, lead, business)

    # TODO: Extract qualification data
    return ai_text
