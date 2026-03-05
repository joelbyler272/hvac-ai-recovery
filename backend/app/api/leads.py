import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_business
from app.models.business import Business
from app.models.lead import Lead
from app.models.review_request import ReviewRequest
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


@router.post("/{lead_id}/mark-completed")
async def mark_lead_completed(
    lead_id: str,
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db),
):
    """Mark a lead/job as completed. Triggers review request after 2 hours."""
    result = await db.execute(
        select(Lead).where(Lead.id == uuid.UUID(lead_id), Lead.business_id == business.id)
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    await db.execute(
        sa_update(Lead).where(Lead.id == lead.id).values(status="completed")
    )

    review_url = ""
    if getattr(business, "google_place_id", None):
        review_url = f"https://search.google.com/local/writereview?placeid={business.google_place_id}"

    rr = ReviewRequest(
        business_id=business.id,
        lead_id=lead.id,
        phone=lead.phone,
        review_url=review_url,
    )
    db.add(rr)
    await db.flush()

    try:
        from app.worker.tasks import celery_app
        celery_app.send_task("send_review_request", args=[str(rr.id)], countdown=2 * 3600)
    except Exception:
        pass

    return {"status": "completed", "review_request_id": str(rr.id)}


@router.post("/{lead_id}/request-review")
async def request_review_manually(
    lead_id: str,
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger a review request (sent immediately)."""
    result = await db.execute(
        select(Lead).where(Lead.id == uuid.UUID(lead_id), Lead.business_id == business.id)
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    review_url = ""
    if getattr(business, "google_place_id", None):
        review_url = f"https://search.google.com/local/writereview?placeid={business.google_place_id}"

    rr = ReviewRequest(
        business_id=business.id,
        lead_id=lead.id,
        phone=lead.phone,
        review_url=review_url,
    )
    db.add(rr)
    await db.flush()

    try:
        from app.worker.tasks import celery_app
        celery_app.send_task("send_review_request", args=[str(rr.id)])
    except Exception:
        pass

    return {"status": "review_requested", "review_request_id": str(rr.id)}
