from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from app.middleware.auth import get_current_business
from app.models.business import Business

router = APIRouter()


class CreateAppointmentRequest(BaseModel):
    lead_id: str
    scheduled_date: str
    scheduled_time: str
    service_type: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None


@router.get("/")
async def list_appointments(
    business: Business = Depends(get_current_business),
):
    """List appointments."""
    # TODO: Implement appointments query
    return {"appointments": []}


@router.post("/")
async def create_appointment(
    request: CreateAppointmentRequest,
    business: Business = Depends(get_current_business),
):
    """Create appointment manually."""
    # TODO: Implement appointment creation
    return {"appointment": None}


@router.patch("/{appointment_id}")
async def update_appointment(
    appointment_id: str, business: Business = Depends(get_current_business)
):
    """Update appointment status."""
    # TODO: Implement appointment update
    return {"appointment": None}
