"""Subscription status guard — blocks API access for inactive businesses."""

from fastapi import HTTPException

from app.models.business import Business


def require_active_subscription(business: Business) -> None:
    """Raise 403 if the business subscription is not active."""
    if business.subscription_status not in ("active", "trialing"):
        raise HTTPException(
            status_code=403,
            detail=f"Subscription is {business.subscription_status}. Please update your billing to continue.",
        )
