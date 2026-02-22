import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_business
from app.models.business import Business
from app.services.crud import get_leads, get_lead_detail, update_lead
from app.api.schemas import lead_to_dict, convo_to_dict, msg_to_dict

router = APIRouter()


@router.get("/")
async def list_leads(
    status: Optional[str] = None,
    page: int = 1,
    per_page: int = 50,
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db),
):
    """List leads, filterable by status."""
    leads = await get_leads(db, business.id, status=status, page=page, per_page=per_page)
    return {"leads": [lead_to_dict(l) for l in leads]}


@router.get("/{lead_id}")
async def get_lead(
    lead_id: str,
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db),
):
    """Lead detail with conversation history."""
    result = await get_lead_detail(db, business.id, uuid.UUID(lead_id))
    if not result:
        raise HTTPException(status_code=404, detail="Lead not found")

    lead, conversations, messages = result
    return {
        "lead": lead_to_dict(lead),
        "conversations": [convo_to_dict(c) for c in conversations],
        "messages": [msg_to_dict(m) for m in messages],
    }


@router.patch("/{lead_id}")
async def update_lead_endpoint(
    lead_id: str,
    request: Request,
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db),
):
    """Update lead status or notes."""
    body = await request.json()
    allowed = {"status", "name", "service_needed", "urgency", "address", "notes", "preferred_time"}
    update_data = {k: v for k, v in body.items() if k in allowed}

    lead = await update_lead(db, business.id, uuid.UUID(lead_id), **update_data)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"lead": lead_to_dict(lead)}
