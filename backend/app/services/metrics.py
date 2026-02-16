import uuid
from datetime import date


async def compute_daily_metrics(business_id: uuid.UUID, for_date: date) -> dict:
    """Compute daily metrics for a business."""
    # TODO: Implement metrics computation from calls, leads, etc.
    return {
        "total_calls": 0,
        "missed_calls": 0,
        "recovered_calls": 0,
        "leads_captured": 0,
        "leads_qualified": 0,
        "appointments_booked": 0,
        "estimated_revenue": 0,
        "messages_sent": 0,
        "messages_received": 0,
    }
