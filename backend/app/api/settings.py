from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_business
from app.models.business import Business
from app.services.crud import update_business

router = APIRouter()


@router.get("/")
async def get_settings_endpoint(
    business: Business = Depends(get_current_business),
):
    """Get business settings."""
    return {
        "settings": {
            "name": business.name,
            "owner_name": business.owner_name,
            "owner_email": business.owner_email,
            "owner_phone": business.owner_phone,
            "business_phone": business.business_phone,
            "twilio_number": business.twilio_number,
            "timezone": business.timezone,
            "business_hours": business.business_hours,
            "services": business.services,
            "avg_job_value": float(business.avg_job_value) if business.avg_job_value else 350.0,
            "ai_greeting": business.ai_greeting,
            "ai_instructions": business.ai_instructions,
            "notification_prefs": business.notification_prefs,
        }
    }


@router.patch("/")
async def update_settings_endpoint(
    request: Request,
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db),
):
    """Update business settings."""
    body = await request.json()
    allowed = {
        "name", "owner_name", "owner_email", "owner_phone",
        "business_hours", "services", "avg_job_value",
        "ai_greeting", "ai_instructions", "notification_prefs", "timezone",
    }
    update_data = {k: v for k, v in body.items() if k in allowed}
    await update_business(db, business.id, **update_data)

    return await get_settings_endpoint(business=business)
