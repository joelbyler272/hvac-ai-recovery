import uuid

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.business import Business
from app.api.schemas import biz_to_dict

settings = get_settings()
router = APIRouter()


async def verify_admin(x_admin_key: str = Header()):
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Invalid admin key")


class OnboardBusinessRequest(BaseModel):
    name: str
    owner_name: str
    owner_email: str
    owner_phone: str
    business_phone: str
    twilio_number: str
    timezone: str = "America/New_York"
    services: list[str] = []


@router.get("/businesses")
async def list_businesses(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin),
):
    """List all client businesses."""
    result = await db.execute(select(Business).order_by(Business.created_at.desc()))
    businesses = result.scalars().all()
    return {"businesses": [biz_to_dict(b) for b in businesses]}


@router.post("/businesses")
async def onboard_business(
    request: OnboardBusinessRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin),
):
    """Onboard a new client business."""
    business = Business(
        name=request.name,
        owner_name=request.owner_name,
        owner_email=request.owner_email,
        owner_phone=request.owner_phone,
        business_phone=request.business_phone,
        twilio_number=request.twilio_number,
        timezone=request.timezone,
        services=request.services,
    )
    db.add(business)
    await db.flush()
    return {"business": biz_to_dict(business)}


@router.patch("/businesses/{business_id}")
async def update_business_endpoint(
    business_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin),
):
    """Update client configuration."""
    body = await request.json()
    result = await db.execute(
        select(Business).where(Business.id == uuid.UUID(business_id))
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    for key, value in body.items():
        if hasattr(business, key):
            setattr(business, key, value)
    await db.flush()

    return {"business": biz_to_dict(business)}


@router.post("/businesses/{business_id}/provision")
async def provision_number(
    business_id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin),
):
    """Provision a Twilio number for a business."""
    return {"message": "Twilio provisioning requires API credentials. Use Twilio console for now."}


@router.get("/health")
async def system_health():
    """System health check."""
    return {"status": "healthy"}


@router.get("/metrics")
async def system_metrics(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin),
):
    """Cross-client metrics."""
    from sqlalchemy import func
    from app.models.call import Call
    from app.models.lead import Lead

    total_businesses = (await db.execute(
        select(func.count(Business.id))
    )).scalar() or 0
    total_calls = (await db.execute(
        select(func.count(Call.id))
    )).scalar() or 0
    total_leads = (await db.execute(
        select(func.count(Lead.id))
    )).scalar() or 0

    return {
        "metrics": {
            "total_businesses": total_businesses,
            "total_calls": total_calls,
            "total_leads": total_leads,
        }
    }
