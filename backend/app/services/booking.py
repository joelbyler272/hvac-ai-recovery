import uuid
from datetime import date, datetime, time, timedelta

import pytz
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business import Business
from app.models.appointment import Appointment
from app.models.lead import Lead


async def get_available_slots(
    db: AsyncSession,
    business_id: uuid.UUID,
    days_ahead: int = 3,
    duration_minutes: int = 60,
) -> list[dict]:
    """Get available appointment slots for the next N business days."""
    biz_result = await db.execute(
        select(Business).where(Business.id == business_id)
    )
    business = biz_result.scalar_one_or_none()
    if not business:
        return []

    tz = pytz.timezone(business.timezone)
    now = datetime.now(tz)
    slots = []
    day_offset = 0
    business_days_found = 0

    while business_days_found < days_ahead and day_offset < 14:
        check_date = (now + timedelta(days=day_offset)).date()

        # Skip today if past 3pm
        if day_offset == 0 and now.hour >= 15:
            day_offset += 1
            continue

        day_name = check_date.strftime("%A").lower()
        hours = business.business_hours.get(day_name)

        if hours:
            open_time = datetime.strptime(hours["open"], "%H:%M").time()
            close_time = datetime.strptime(hours["close"], "%H:%M").time()

            # Get existing appointments for this date
            existing = await db.execute(
                select(Appointment.scheduled_time).where(
                    Appointment.business_id == business_id,
                    Appointment.scheduled_date == check_date,
                    Appointment.status.in_(["scheduled", "confirmed"]),
                )
            )
            booked_times = {row[0] for row in existing.all()}

            # Generate slots based on duration
            slot_step = max(duration_minutes, 30)  # minimum 30-min steps
            open_minutes = open_time.hour * 60 + open_time.minute
            close_minutes = close_time.hour * 60 + close_time.minute

            if day_offset == 0:
                earliest = (now.hour + 1) * 60
                open_minutes = max(open_minutes, earliest)

            current_minutes = open_minutes
            while current_minutes + duration_minutes <= close_minutes:
                slot_hour = current_minutes // 60
                slot_min = current_minutes % 60
                slot_time = time(slot_hour, slot_min)

                # Check if slot overlaps with any booked appointment
                slot_conflicts = False
                for booked_time in booked_times:
                    booked_start = booked_time.hour * 60 + booked_time.minute
                    # Assume booked appointments are ~60 min (safe overlap check)
                    if not (current_minutes + duration_minutes <= booked_start or current_minutes >= booked_start + 60):
                        slot_conflicts = True
                        break

                if not slot_conflicts:
                    slots.append(
                        {
                            "date": check_date.strftime("%a %b %d"),
                            "time": slot_time.strftime("%I:%M %p").lstrip("0"),
                            "date_iso": check_date.isoformat(),
                            "time_iso": slot_time.isoformat(),
                            "duration_minutes": duration_minutes,
                        }
                    )
                current_minutes += slot_step

            business_days_found += 1

        day_offset += 1

    return slots


def format_slots_for_sms(slots: list) -> str:
    """Format available time slots for SMS display."""
    if not slots:
        return "No available slots right now."

    lines = []
    for i, slot in enumerate(slots, 1):
        lines.append(f"{i}. {slot['date']} at {slot['time']}")
    return "\n".join(lines)


async def offer_booking(
    db: AsyncSession,
    conversation,
    lead: Lead,
    business: Business,
    service=None,
) -> str:
    """Offer available time slots to a qualified lead."""
    duration = service.duration_minutes if service else 60
    slots = await get_available_slots(db, business.id, days_ahead=3, duration_minutes=duration)

    if not slots:
        return (
            "Great, I've got all your info! Someone from our team will "
            "call you shortly to confirm a time."
        )

    slot_text = format_slots_for_sms(slots[:4])

    # Frame differently for estimate-required vs bookable services
    if service and not service.is_bookable:
        intro = "We'd love to get a free estimate visit scheduled for you!"
    elif service and service.is_bookable and service.price:
        intro = f"Awesome, we'd love to get your {service.name} (${service.price:.0f}) scheduled!"
    else:
        intro = "Awesome, we'd love to get you scheduled!"

    return (
        f"{intro} "
        f"Here are some openings:\n\n{slot_text}\n\n"
        f"Which works best, or is there another time you'd prefer?"
    )
