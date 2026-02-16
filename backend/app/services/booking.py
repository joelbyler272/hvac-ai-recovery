import uuid

from app.models.business import Business
from app.models.lead import Lead


async def get_available_slots(business_id: uuid.UUID, days_ahead: int = 3) -> list:
    """Get available appointment slots for the next N business days."""
    # TODO: Implement slot generation based on business hours
    # For MVP, generate 1-hour slots during business hours
    return []


def format_slots_for_sms(slots: list) -> str:
    """Format available time slots for SMS display."""
    if not slots:
        return "No available slots right now."

    lines = []
    for i, slot in enumerate(slots, 1):
        lines.append(f"{i}. {slot['date']} at {slot['time']}")
    return "\n".join(lines)


async def offer_booking(conversation, lead: Lead, business: Business) -> str:
    """Offer available time slots to a qualified lead."""
    slots = await get_available_slots(business.id, days_ahead=3)

    if not slots:
        return (
            "Great, I've got all your info! Someone from our team will "
            "call you shortly to confirm a time."
        )

    slot_text = format_slots_for_sms(slots[:4])
    return (
        f"Awesome, we'd love to get you scheduled! "
        f"Here are some openings:\n\n{slot_text}\n\n"
        f"Which works best, or is there another time you'd prefer?"
    )
