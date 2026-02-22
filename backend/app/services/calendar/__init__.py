"""Calendar integration module — provider factory and helpers."""
import logging
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calendar_integration import CalendarIntegration
from app.services.calendar.base import CalendarProvider, CalendarEvent
from app.services.calendar.google import GoogleCalendarProvider
from app.services.calendar.outlook import OutlookCalendarProvider

logger = logging.getLogger(__name__)

_providers: dict[str, CalendarProvider] = {}


def get_calendar_provider(provider_name: str) -> CalendarProvider:
    """Factory — returns a CalendarProvider instance by name."""
    if provider_name not in _providers:
        if provider_name == "google":
            _providers[provider_name] = GoogleCalendarProvider()
        elif provider_name == "outlook":
            _providers[provider_name] = OutlookCalendarProvider()
        else:
            raise ValueError(f"Unknown calendar provider: {provider_name}")
    return _providers[provider_name]


async def _ensure_valid_token(
    db: AsyncSession, integration: CalendarIntegration
) -> str:
    """Refresh the access token if expired; return a valid token."""
    if integration.token_expires_at and integration.token_expires_at > datetime.utcnow():
        return integration.access_token

    provider = get_calendar_provider(integration.provider)
    try:
        result = await provider.refresh_access_token(integration.refresh_token)
        integration.access_token = result["access_token"]
        integration.token_expires_at = result["expires_at"]
        await db.flush()
        return result["access_token"]
    except Exception as e:
        logger.error(f"Failed to refresh {integration.provider} token: {e}")
        raise


async def push_appointment_to_calendar(
    db: AsyncSession,
    appointment,
    business,
    lead=None,
) -> str | None:
    """Push an appointment to all active calendar integrations.

    Returns the calendar_event_id if created, or None.
    """
    integrations_result = await db.execute(
        select(CalendarIntegration).where(
            CalendarIntegration.business_id == business.id,
            CalendarIntegration.is_active == True,
        )
    )
    integrations = integrations_result.scalars().all()

    if not integrations:
        return None

    lead_name = lead.name if lead else "Customer"
    service = appointment.service_type or "HVAC Service"
    title = f"{service} — {lead_name}"
    description = f"Appointment for {lead_name}\nService: {service}"
    if appointment.address:
        description += f"\nAddress: {appointment.address}"
    if appointment.notes:
        description += f"\nNotes: {appointment.notes}"

    start_dt = datetime.combine(appointment.scheduled_date, appointment.scheduled_time)
    end_dt = start_dt + timedelta(minutes=appointment.duration_minutes)

    event_id = None
    for integration in integrations:
        try:
            token = await _ensure_valid_token(db, integration)
            provider = get_calendar_provider(integration.provider)
            event = await provider.create_event(
                access_token=token,
                calendar_id=integration.calendar_id or "primary",
                title=title,
                start=start_dt,
                end=end_dt,
                description=description,
            )
            event_id = event.id
            logger.info(f"Created {integration.provider} calendar event: {event.id}")
        except Exception as e:
            logger.error(f"Failed to push appointment to {integration.provider}: {e}")

    return event_id
