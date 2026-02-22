"""Serialization helpers for API responses."""
from decimal import Decimal


def _serialize(val):
    if val is None:
        return None
    if isinstance(val, Decimal):
        return float(val)
    return val


def lead_to_dict(lead) -> dict:
    return {
        "id": str(lead.id),
        "business_id": str(lead.business_id),
        "phone": lead.phone,
        "name": lead.name,
        "email": lead.email,
        "address": lead.address,
        "service_needed": lead.service_needed,
        "urgency": lead.urgency,
        "status": lead.status,
        "source": lead.source,
        "estimated_value": float(lead.estimated_value) if lead.estimated_value else None,
        "preferred_time": lead.preferred_time,
        "notes": lead.notes,
        "created_at": lead.created_at.isoformat() if lead.created_at else None,
        "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
    }


def convo_to_dict(convo, lead=None) -> dict:
    d = {
        "id": str(convo.id),
        "business_id": str(convo.business_id),
        "lead_id": str(convo.lead_id),
        "call_id": str(convo.call_id) if convo.call_id else None,
        "status": convo.status,
        "follow_up_count": convo.follow_up_count,
        "next_follow_up_at": convo.next_follow_up_at.isoformat() if convo.next_follow_up_at else None,
        "qualification_data": convo.qualification_data,
        "created_at": convo.created_at.isoformat() if convo.created_at else None,
        "updated_at": convo.updated_at.isoformat() if convo.updated_at else None,
    }
    if lead:
        d["lead"] = lead_to_dict(lead)
    return d


def msg_to_dict(msg) -> dict:
    return {
        "id": str(msg.id),
        "conversation_id": str(msg.conversation_id),
        "direction": msg.direction,
        "sender_type": msg.sender_type,
        "body": msg.body,
        "twilio_message_sid": msg.twilio_message_sid,
        "status": msg.status,
        "created_at": msg.created_at.isoformat() if msg.created_at else None,
    }


def call_to_dict(call) -> dict:
    return {
        "id": str(call.id),
        "business_id": str(call.business_id),
        "twilio_call_sid": call.twilio_call_sid,
        "caller_phone": call.caller_phone,
        "status": call.status,
        "duration_seconds": call.duration_seconds,
        "is_after_hours": call.is_after_hours,
        "recording_url": call.recording_url,
        "transcription": call.transcription,
        "created_at": call.created_at.isoformat() if call.created_at else None,
    }


def appt_to_dict(appt) -> dict:
    return {
        "id": str(appt.id),
        "business_id": str(appt.business_id),
        "lead_id": str(appt.lead_id),
        "conversation_id": str(appt.conversation_id) if appt.conversation_id else None,
        "scheduled_date": appt.scheduled_date.isoformat() if appt.scheduled_date else None,
        "scheduled_time": appt.scheduled_time.isoformat() if appt.scheduled_time else None,
        "duration_minutes": appt.duration_minutes,
        "service_type": appt.service_type,
        "address": appt.address,
        "status": appt.status,
        "notes": appt.notes,
        "created_at": appt.created_at.isoformat() if appt.created_at else None,
        "updated_at": appt.updated_at.isoformat() if appt.updated_at else None,
    }


def metric_to_dict(m) -> dict:
    return {
        "id": str(m.id),
        "date": m.date.isoformat() if m.date else None,
        "total_calls": m.total_calls,
        "missed_calls": m.missed_calls,
        "recovered_calls": m.recovered_calls,
        "leads_captured": m.leads_captured,
        "leads_qualified": m.leads_qualified,
        "appointments_booked": m.appointments_booked,
        "estimated_revenue": float(m.estimated_revenue) if m.estimated_revenue else 0,
        "messages_sent": m.messages_sent,
        "messages_received": m.messages_received,
    }


def biz_to_dict(b) -> dict:
    return {
        "id": str(b.id),
        "name": b.name,
        "owner_name": b.owner_name,
        "owner_email": b.owner_email,
        "owner_phone": b.owner_phone,
        "business_phone": b.business_phone,
        "twilio_number": b.twilio_number,
        "timezone": b.timezone,
        "business_hours": b.business_hours,
        "services": b.services,
        "avg_job_value": float(b.avg_job_value) if b.avg_job_value else 350.0,
        "ai_greeting": b.ai_greeting,
        "ai_instructions": b.ai_instructions,
        "notification_prefs": b.notification_prefs,
        "subscription_status": b.subscription_status,
        "created_at": b.created_at.isoformat() if b.created_at else None,
        "updated_at": b.updated_at.isoformat() if b.updated_at else None,
    }


def service_to_dict(s) -> dict:
    return {
        "id": str(s.id),
        "business_id": str(s.business_id),
        "name": s.name,
        "description": s.description,
        "price": float(s.price) if s.price else None,
        "duration_minutes": s.duration_minutes,
        "is_bookable": s.is_bookable,
        "is_active": s.is_active,
        "sort_order": s.sort_order,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


def activity_to_dict(item_type: str, item) -> dict:
    """Convert a call, message, or lead into a generic activity item."""
    if item_type == "call":
        return {
            "type": "call",
            "id": str(item.id),
            "description": f"{'Missed' if item.status == 'missed' else 'Answered'} call from {item.caller_phone}",
            "status": item.status,
            "phone": item.caller_phone,
            "timestamp": item.created_at.isoformat() if item.created_at else None,
        }
    elif item_type == "message":
        direction = "Received" if item.direction == "inbound" else "Sent"
        return {
            "type": "message",
            "id": str(item.id),
            "description": f"{direction} SMS ({item.sender_type})",
            "body_preview": item.body[:80] + "..." if len(item.body) > 80 else item.body,
            "direction": item.direction,
            "sender_type": item.sender_type,
            "timestamp": item.created_at.isoformat() if item.created_at else None,
        }
    elif item_type == "lead":
        return {
            "type": "lead",
            "id": str(item.id),
            "description": f"Lead {item.status}: {item.name or item.phone}",
            "status": item.status,
            "phone": item.phone,
            "name": item.name,
            "timestamp": item.updated_at.isoformat() if item.updated_at else None,
        }
    return {}
