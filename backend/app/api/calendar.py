"""Calendar integration API endpoints."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.middleware.auth import get_current_business
from app.models.business import Business
from app.models.calendar_integration import CalendarIntegration
from app.services.calendar import get_calendar_provider

router = APIRouter()
settings = get_settings()


def _calendar_to_dict(integration: CalendarIntegration) -> dict:
    return {
        "id": str(integration.id),
        "business_id": str(integration.business_id),
        "provider": integration.provider,
        "calendar_id": integration.calendar_id,
        "is_active": integration.is_active,
        "last_sync_at": integration.last_sync_at.isoformat() if integration.last_sync_at else None,
        "created_at": integration.created_at.isoformat() if integration.created_at else None,
    }


@router.get("/integrations")
async def list_integrations(
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db),
):
    """List connected calendar integrations."""
    result = await db.execute(
        select(CalendarIntegration).where(
            CalendarIntegration.business_id == business.id,
            CalendarIntegration.is_active == True,
        )
    )
    integrations = result.scalars().all()
    return {"integrations": [_calendar_to_dict(i) for i in integrations]}


@router.get("/connect/{provider}")
async def connect_calendar(
    provider: str,
    business: Business = Depends(get_current_business),
):
    """Get OAuth authorization URL for a calendar provider."""
    if provider not in ("google", "outlook"):
        raise HTTPException(status_code=400, detail="Unsupported provider. Use 'google' or 'outlook'.")

    cal_provider = get_calendar_provider(provider)
    base_url = settings.base_url.rstrip("/")
    redirect_uri = f"{base_url}/api/calendar/callback/{provider}"
    state = f"{business.id}:{provider}"

    auth_url = await cal_provider.get_auth_url(redirect_uri, state)
    return {"auth_url": auth_url}


@router.get("/callback/{provider}")
async def calendar_callback(
    provider: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle OAuth callback from calendar provider."""
    code = request.query_params.get("code")
    state = request.query_params.get("state")

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state parameter")

    try:
        business_id_str, _ = state.split(":", 1)
        business_id = uuid.UUID(business_id_str)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    cal_provider = get_calendar_provider(provider)
    base_url = settings.base_url.rstrip("/")
    redirect_uri = f"{base_url}/api/calendar/callback/{provider}"

    try:
        tokens = await cal_provider.exchange_code(code, redirect_uri)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to exchange code: {str(e)}")

    # Upsert the calendar integration
    result = await db.execute(
        select(CalendarIntegration).where(
            CalendarIntegration.business_id == business_id,
            CalendarIntegration.provider == provider,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.access_token = tokens["access_token"]
        existing.refresh_token = tokens.get("refresh_token", existing.refresh_token)
        existing.token_expires_at = tokens["expires_at"]
        existing.is_active = True
        existing.calendar_id = "primary"
    else:
        integration = CalendarIntegration(
            business_id=business_id,
            provider=provider,
            access_token=tokens["access_token"],
            refresh_token=tokens.get("refresh_token", ""),
            token_expires_at=tokens["expires_at"],
            calendar_id="primary",
            is_active=True,
        )
        db.add(integration)

    await db.flush()

    # Redirect to settings page with success indicator
    frontend_url = "http://localhost:3002"  # TODO: make configurable
    return {"message": "Calendar connected successfully", "redirect": f"{frontend_url}/settings?calendar=connected"}


@router.delete("/integrations/{integration_id}")
async def disconnect_calendar(
    integration_id: str,
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db),
):
    """Disconnect a calendar integration."""
    result = await db.execute(
        select(CalendarIntegration).where(
            CalendarIntegration.id == uuid.UUID(integration_id),
            CalendarIntegration.business_id == business.id,
        )
    )
    integration = result.scalar_one_or_none()

    if not integration:
        raise HTTPException(status_code=404, detail="Calendar integration not found")

    integration.is_active = False
    await db.flush()

    return {"deleted": True}
