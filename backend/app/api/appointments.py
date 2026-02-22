import uuid
from datetime import date, time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_business
from app.models.business import Business
from app.models.lead import Lead
from app.services.crud import get_appointments, create_appointment, update_appointment
from app.api.schemas import appt_to_dict

router = APIRouter()


class CreateAppointmentRequest(BaseModel):
    lead_id: str
    scheduled_date: str
    scheduled_time: str
    service_type: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    conversation_id: Optional[str] = None


@router.get("/")
async def list_appointments(
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db),
):
    """List appointments."""
    appts = await get_appointments(db, business.id)
    return {"appointments": [appt_to_dict(a) for a in appts]}


@router.post("/")
async def create_appointment_endpoint(
    request: CreateAppointmentRequest,
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db),
):
    """Create appointment manually."""
    scheduled_date = date.fromisoformat(request.scheduled_date)
    if scheduled_date < date.today():
        raise HTTPException(status_code=400, detail="Cannot schedule appointments in the past")

    appt = await create_appointment(
        db,
        business.id,
        lead_id=uuid.UUID(request.lead_id),
        scheduled_date=scheduled_date,
        scheduled_time=time.fromisoformat(request.scheduled_time),
        service_type=request.service_type,
        address=request.address,
        notes=request.notes,
        conversation_id=uuid.UUID(request.conversation_id) if request.conversation_id else None,
    )
    # Update lead status to booked
    await db.execute(
        sa_update(Lead)
        .where(Lead.id == uuid.UUID(request.lead_id))
        .values(status="booked")
    )
    return {"appointment": appt_to_dict(appt)}


@router.patch("/{appointment_id}")
async def update_appointment_endpoint(
    appointment_id: str,
    request: Request,
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db),
):
    """Update appointment status."""
    body = await request.json()
    allowed = {"status", "scheduled_date", "scheduled_time", "notes", "service_type", "address"}
    update_data = {k: v for k, v in body.items() if k in allowed}
    appt = await update_appointment(db, business.id, uuid.UUID(appointment_id), **update_data)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"appointment": appt_to_dict(appt)}
