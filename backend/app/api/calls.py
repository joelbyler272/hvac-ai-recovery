from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_business
from app.models.business import Business
from app.services.crud import get_calls
from app.api.schemas import call_to_dict

router = APIRouter()


@router.get("/")
async def list_calls(
    status: str | None = None,
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db),
):
    """List calls for the business."""
    calls = await get_calls(db, business.id, status=status)
    return {"calls": [call_to_dict(c) for c in calls]}
