from fastapi import APIRouter, Depends

from app.middleware.auth import get_current_business
from app.models.business import Business

router = APIRouter()


@router.get("/weekly")
async def weekly_report(business: Business = Depends(get_current_business)):
    """Weekly summary report."""
    # TODO: Implement weekly report
    return {"report": None}


@router.get("/monthly")
async def monthly_report(business: Business = Depends(get_current_business)):
    """Monthly summary with ROI calculation."""
    # TODO: Implement monthly report
    return {"report": None}
