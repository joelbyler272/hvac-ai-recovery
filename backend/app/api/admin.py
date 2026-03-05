import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.business import Business
from app.api.schemas import biz_to_dict

logger = logging.getLogger(__name__)
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


@router.post("/businesses/{business_id}/configure-voice")
async def configure_voice_ai(
    business_id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin),
):
    """
    Create or update the Vapi voice AI assistant for a business.

    This sets up the voice AI with the business's specific configuration:
    services, hours, custom prompt, voice selection, etc.
    """
    from app.services.vapi import create_or_update_assistant, VapiUnavailableError

    result = await db.execute(
        select(Business).where(Business.id == uuid.UUID(business_id))
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    if not settings.vapi_api_key:
        raise HTTPException(
            status_code=400,
            detail="VAPI_API_KEY not configured. Set it in environment variables.",
        )

    try:
        assistant_id = await create_or_update_assistant(db, business)
        return {
            "status": "configured",
            "vapi_assistant_id": assistant_id,
            "business_id": business_id,
        }
    except VapiUnavailableError as e:
        raise HTTPException(status_code=502, detail=f"Vapi API error: {e}")


@router.post("/businesses/{business_id}/test-call")
async def test_voice_call(
    business_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin),
):
    """
    Initiate a test call to verify the voice AI is working.

    Request body: {"phone_number": "+1234567890"}
    The specified number will receive a call from the Vapi voice AI assistant.
    """
    from app.services.vapi import transfer_call_to_vapi, VapiUnavailableError

    result = await db.execute(
        select(Business).where(Business.id == uuid.UUID(business_id))
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    if not business.vapi_assistant_id:
        raise HTTPException(
            status_code=400,
            detail="Voice AI not configured. Call /configure-voice first.",
        )

    body = await request.json()
    phone_number = body.get("phone_number")
    if not phone_number:
        raise HTTPException(status_code=400, detail="phone_number is required")

    try:
        # Create a temporary call ID for tracking
        test_call_id = uuid.uuid4()
        vapi_call_id = await transfer_call_to_vapi(
            business=business,
            caller_phone=phone_number,
            call_id=test_call_id,
        )
        return {
            "status": "call_initiated",
            "vapi_call_id": vapi_call_id,
            "phone_number": phone_number,
            "message": "Test call initiated. The phone number will receive a call from the voice AI.",
        }
    except VapiUnavailableError as e:
        raise HTTPException(status_code=502, detail=f"Vapi call failed: {e}")


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
    health = {"status": "healthy", "vapi_configured": bool(settings.vapi_api_key)}
    return health


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
    voice_ai_calls = (await db.execute(
        select(func.count(Call.id)).where(Call.voice_ai_used == True)
    )).scalar() or 0

    return {
        "metrics": {
            "total_businesses": total_businesses,
            "total_calls": total_calls,
            "total_leads": total_leads,
            "voice_ai_calls": voice_ai_calls,
        }
    }
