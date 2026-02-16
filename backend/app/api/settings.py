from fastapi import APIRouter, Depends

from app.middleware.auth import get_current_business
from app.models.business import Business

router = APIRouter()


@router.get("/")
async def get_settings(business: Business = Depends(get_current_business)):
    """Get business settings."""
    # TODO: Return business settings
    return {"settings": None}


@router.patch("/")
async def update_settings(business: Business = Depends(get_current_business)):
    """Update business settings (hours, AI greeting, notifications, etc.)."""
    # TODO: Implement settings update
    return {"settings": None}
