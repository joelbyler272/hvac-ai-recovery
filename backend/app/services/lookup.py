"""
Twilio Lookup API integration for phone number line type detection.

Determines if a caller's phone is mobile, landline, or VoIP.
This affects post-call behavior:
- Mobile: can send SMS confirmations and follow-ups
- Landline: voice only, no SMS possible
- VoIP: treat as mobile (most VoIP can receive SMS)
"""

import logging

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_twilio_client = None


def _get_twilio_client():
    global _twilio_client
    if _twilio_client is None:
        from twilio.rest import Client
        _twilio_client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    return _twilio_client


async def detect_line_type(phone_number: str) -> str:
    """
    Detect the line type of a phone number using Twilio Lookup API v2.

    Cost: ~$0.005 per lookup.

    Returns one of: "mobile", "landline", "voip", "unknown"
    """
    if not settings.twilio_account_sid or not settings.twilio_auth_token:
        return "unknown"

    try:
        client = _get_twilio_client()
        # Twilio Lookup v2 with line_type_intelligence add-on
        result = client.lookups.v2.phone_numbers(phone_number).fetch(
            fields="line_type_intelligence"
        )

        line_type_result = getattr(result, "line_type_intelligence", None)
        if line_type_result and isinstance(line_type_result, dict):
            carrier_type = line_type_result.get("type", "unknown")
            # Normalize the type values
            type_map = {
                "mobile": "mobile",
                "landline": "landline",
                "fixedVoip": "voip",
                "nonFixedVoip": "voip",
                "voip": "voip",
                "tollFree": "landline",
                "premium": "landline",
                "sharedCost": "landline",
                "personalNumber": "mobile",
                "pager": "landline",
            }
            return type_map.get(carrier_type, "unknown")

        return "unknown"

    except Exception as e:
        logger.warning(f"Twilio Lookup failed for {phone_number}: {e}")
        return "unknown"


def can_receive_sms(line_type: str) -> bool:
    """Check if a line type can receive SMS messages."""
    return line_type in ("mobile", "voip", "unknown")
