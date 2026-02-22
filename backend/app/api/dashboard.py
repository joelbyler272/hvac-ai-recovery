from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_business
from app.models.business import Business
from app.services.crud import get_dashboard_stats, get_recent_activity

router = APIRouter()


@router.get("/stats")
async def get_stats(
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db),
):
    """Summary metrics: calls, leads, revenue."""
    stats = await get_dashboard_stats(db, business.id)
    return stats


@router.get("/recent")
async def get_recent(
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db),
):
    """Recent activity feed."""
    activities = await get_recent_activity(db, business.id, limit=20)
    return {"activities": activities}
