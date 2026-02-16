from fastapi import APIRouter, Depends
from typing import Optional

from app.middleware.auth import get_current_business
from app.models.business import Business

router = APIRouter()


@router.get("/")
async def list_leads(
    status: Optional[str] = None,
    business: Business = Depends(get_current_business),
):
    """List leads, filterable by status."""
    # TODO: Implement leads query
    return {"leads": []}


@router.get("/{lead_id}")
async def get_lead(lead_id: str, business: Business = Depends(get_current_business)):
    """Lead detail with full conversation."""
    # TODO: Implement lead detail
    return {"lead": None}


@router.patch("/{lead_id}")
async def update_lead(
    lead_id: str, business: Business = Depends(get_current_business)
):
    """Update lead status or notes."""
    # TODO: Implement lead update
    return {"lead": None}
