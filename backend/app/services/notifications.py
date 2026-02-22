import logging
from datetime import datetime, time

import pytz

from app.config import get_settings
from app.models.business import Business

logger = logging.getLogger(__name__)
settings = get_settings()


def format_phone(phone: str) -> str:
    """Format phone number for display."""
    if len(phone) == 12 and phone.startswith("+1"):
        digits = phone[2:]
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return phone


def is_in_quiet_hours(current_time: time, quiet_start: time, quiet_end: time) -> bool:
    """Check if current time falls within quiet hours."""
    if quiet_start <= quiet_end:
        return quiet_start <= current_time <= quiet_end
    else:  # Spans midnight (e.g., 21:00 to 07:00)
        return current_time >= quiet_start or current_time <= quiet_end


async def notify_owner(business: Business, event: str, data: dict) -> None:
    """Send notification to business owner based on preferences."""
    prefs = business.notification_prefs or {}
    now = datetime.now(pytz.timezone(business.timezone))

    quiet_start_str = prefs.get("quiet_start", "21:00")
    quiet_end_str = prefs.get("quiet_end", "07:00")
    quiet_start = datetime.strptime(quiet_start_str, "%H:%M").time()
    quiet_end = datetime.strptime(quiet_end_str, "%H:%M").time()
    in_quiet = is_in_quiet_hours(now.time(), quiet_start, quiet_end)

    message = build_notification_message(event, data, business)

    # SMS notification (unless quiet hours — emergency overrides)
    if prefs.get("sms", True) and (not in_quiet or event == "emergency"):
        try:
            from app.services.sms import _get_twilio_client

            client = _get_twilio_client()
            client.messages.create(
                to=business.owner_phone,
                from_=business.twilio_number,
                body=message,
            )
        except Exception as e:
            logger.warning(f"Failed to send SMS notification: {e}")

    # Email notification (always, unless disabled)
    if prefs.get("email", True) and settings.resend_api_key:
        try:
            import resend

            resend.api_key = settings.resend_api_key
            resend.Emails.send(
                {
                    "from": settings.email_from_address,
                    "to": business.owner_email,
                    "subject": f"CallRecover: {event.replace('_', ' ').title()}",
                    "text": message,
                }
            )
        except Exception as e:
            logger.warning(f"Failed to send email notification: {e}")


def build_notification_message(event: str, data: dict, business: Business) -> str:
    """Build human-readable notification messages."""
    templates = {
        "missed_call": (
            f"Missed call from {format_phone(data.get('caller_phone', ''))}. "
            f"AI is following up now."
        ),
        "qualified_lead": _build_qualified_message(data),
        "appointment_booked": "New appointment booked! Check your dashboard for details.",
        "emergency": _build_emergency_message(data),
        "human_needed": (
            "AI needs help with a conversation. "
            "Please check the dashboard and take over."
        ),
        "new_message": f"New message from {format_phone(data.get('from', ''))}",
    }
    return templates.get(event, f"CallRecover notification: {event}")


def _build_qualified_message(data: dict) -> str:
    lead = data.get("lead")
    if not lead:
        return "New qualified lead! Check your dashboard."
    parts = ["New qualified lead!"]
    if hasattr(lead, "name") and lead.name:
        parts.append(f"Name: {lead.name}")
    if hasattr(lead, "service_needed") and lead.service_needed:
        parts.append(f"Needs: {lead.service_needed}")
    if hasattr(lead, "urgency") and lead.urgency:
        parts.append(f"Urgency: {lead.urgency}")
    if hasattr(lead, "address") and lead.address:
        parts.append(f"Address: {lead.address}")
    if hasattr(lead, "phone") and lead.phone:
        parts.append(f"Phone: {format_phone(lead.phone)}")
    return "\n".join(parts)


def _build_emergency_message(data: dict) -> str:
    lead = data.get("lead")
    if not lead:
        return "EMERGENCY lead! Check dashboard immediately."
    parts = ["EMERGENCY LEAD!"]
    if hasattr(lead, "name") and lead.name:
        parts.append(f"{lead.name}")
    if hasattr(lead, "address") and lead.address:
        parts.append(f"at {lead.address}")
    if hasattr(lead, "service_needed") and lead.service_needed:
        parts.append(f"Issue: {lead.service_needed}")
    if hasattr(lead, "phone") and lead.phone:
        parts.append(f"Phone: {format_phone(lead.phone)}")
    parts.append("CALL THEM IMMEDIATELY")
    return "\n".join(parts)
