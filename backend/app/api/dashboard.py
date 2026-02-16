from fastapi import APIRouter, Depends

from app.middleware.auth import get_current_business
from app.models.business import Business

router = APIRouter()


@router.get("/stats")
async def get_stats(business: Business = Depends(get_current_business)):
    """Summary metrics: calls, leads, revenue."""
    # TODO: Implement dashboard stats query
    return {
        "today": {
            "total_calls": 0,
            "missed_calls": 0,
            "recovered_calls": 0,
            "estimated_revenue": 0,
        },
        "this_month": {
            "total_calls": 0,
            "missed_calls": 0,
            "recovered_calls": 0,
            "estimated_revenue": 0,
        },
    }


@router.get("/recent")
async def get_recent_activity(business: Business = Depends(get_current_business)):
    """Recent activity feed."""
    # TODO: Implement recent activity query
    return {"activities": []}
