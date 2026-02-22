import logging
from fastapi import Request, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.business import Business

logger = logging.getLogger(__name__)
settings = get_settings()


async def get_current_business(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Business:
    """
    Extract business from JWT token.
    All downstream queries use this business_id for multi-tenant scoping.
    """
    # Dev mode bypass: skip auth when no Supabase configured
    if settings.environment == "development" and not settings.supabase_url:
        result = await db.execute(select(Business).limit(1))
        business = result.scalar_one_or_none()
        if business:
            return business
        raise HTTPException(
            status_code=503,
            detail="No business in database. Seed a test business first.",
        )

    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=401, detail="Missing authorization token")

    try:
        from supabase import create_client

        supabase_client = create_client(
            settings.supabase_url, settings.supabase_service_role_key
        )
        user_response = supabase_client.auth.get_user(token)
        user = user_response.user
    except Exception as e:
        logger.warning(f"Auth failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Map Supabase user to business
    result = await db.execute(
        select(Business).where(Business.supabase_user_id == user.id)
    )
    business = result.scalar_one_or_none()

    if not business:
        raise HTTPException(
            status_code=403, detail="No business associated with this account"
        )

    return business
