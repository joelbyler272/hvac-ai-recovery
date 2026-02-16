from app.config import get_settings
from app.models.business import Business

settings = get_settings()


def format_phone(phone: str) -> str:
    """Format phone number for display."""
    if len(phone) == 12 and phone.startswith("+1"):
        digits = phone[2:]
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return phone


async def notify_owner(business: Business, event: str, data: dict) -> None:
    """Send notification to business owner based on preferences."""
    # TODO: Implement notification logic
    # - Check quiet hours
    # - Send SMS notification (via Twilio)
    # - Send email notification (via Resend)
    # - Push to Supabase Realtime for dashboard
    pass


def build_notification_message(event: str, data: dict, business: Business) -> str:
    """Build human-readable notification messages."""
    templates = {
        "missed_call": (
            f"Missed call from {format_phone(data.get('caller_phone', ''))}. "
            f"AI is following up now."
        ),
        "qualified_lead": "New qualified lead! Check your dashboard for details.",
        "appointment_booked": "New appointment booked! Check your dashboard.",
        "emergency": "EMERGENCY lead! Check your dashboard and call them immediately.",
        "human_needed": "AI needs help with a conversation. Please check the dashboard.",
        "new_message": f"New message from {format_phone(data.get('from', ''))}",
    }
    return templates.get(event, f"Notification: {event}")
