from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.middleware.auth import get_current_business
from app.models.business import Business
from app.services.crud import get_daily_metrics_range
from app.api.schemas import metric_to_dict

settings = get_settings()

router = APIRouter()


@router.get("/weekly")
async def weekly_report(
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db),
):
    """Weekly summary report."""
    week_start = date.today() - timedelta(days=7)
    metrics = await get_daily_metrics_range(db, business.id, week_start, date.today())

    return {
        "report": {
            "period_start": week_start.isoformat(),
            "period_end": date.today().isoformat(),
            "total_calls": sum(m.total_calls for m in metrics),
            "missed_calls": sum(m.missed_calls for m in metrics),
            "recovered_calls": sum(m.recovered_calls for m in metrics),
            "leads_captured": sum(m.leads_captured for m in metrics),
            "leads_qualified": sum(m.leads_qualified for m in metrics),
            "appointments_booked": sum(m.appointments_booked for m in metrics),
            "estimated_revenue": float(sum(m.estimated_revenue for m in metrics)),
            "daily_breakdown": [metric_to_dict(m) for m in metrics],
        }
    }


@router.get("/monthly")
async def monthly_report(
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db),
):
    """Monthly summary with ROI calculation."""
    month_start = date.today().replace(day=1)
    metrics = await get_daily_metrics_range(db, business.id, month_start, date.today())

    total_revenue = float(sum(m.estimated_revenue for m in metrics))
    subscription_cost = settings.subscription_cost
    roi = ((total_revenue - subscription_cost) / subscription_cost * 100) if subscription_cost else 0

    return {
        "report": {
            "period_start": month_start.isoformat(),
            "period_end": date.today().isoformat(),
            "total_calls": sum(m.total_calls for m in metrics),
            "missed_calls": sum(m.missed_calls for m in metrics),
            "recovered_calls": sum(m.recovered_calls for m in metrics),
            "leads_captured": sum(m.leads_captured for m in metrics),
            "leads_qualified": sum(m.leads_qualified for m in metrics),
            "appointments_booked": sum(m.appointments_booked for m in metrics),
            "estimated_revenue": total_revenue,
            "roi_percentage": round(roi, 1),
            "daily_breakdown": [metric_to_dict(m) for m in metrics],
        }
    }
