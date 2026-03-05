"""
Stripe webhook handler for subscription lifecycle management.

Events handled:
- invoice.payment_succeeded — marks business active
- invoice.payment_failed — marks business past_due
- customer.subscription.deleted — marks business canceled
- customer.subscription.paused — marks business paused
- customer.subscription.resumed — marks business active
"""

import logging

import stripe
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy import select, update as sa_update

from app.config import get_settings
from app.database import async_session_factory

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()


def _verify_stripe_signature(payload: bytes, sig_header: str) -> dict:
    """Verify Stripe webhook signature and return the event."""
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=500, detail="Stripe webhook secret not configured")
    try:
        return stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook error: {e}")


@router.post("/")
async def stripe_webhook(request: Request):
    """Handle Stripe subscription lifecycle events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    event = _verify_stripe_signature(payload, sig_header)
    event_type = event.get("type", "")

    logger.info(f"Stripe webhook: {event_type}")

    handlers = {
        "invoice.payment_succeeded": _handle_payment_succeeded,
        "invoice.payment_failed": _handle_payment_failed,
        "customer.subscription.deleted": _handle_subscription_deleted,
        "customer.subscription.paused": _handle_subscription_paused,
        "customer.subscription.resumed": _handle_subscription_resumed,
    }

    handler = handlers.get(event_type)
    if handler:
        await handler(event)

    return {"received": True}


async def _update_subscription_status(
    stripe_customer_id: str, status: str
) -> None:
    """Update a business's subscription status by Stripe customer ID."""
    from app.models.business import Business

    async with async_session_factory() as db:
        result = await db.execute(
            select(Business).where(Business.stripe_customer_id == stripe_customer_id)
        )
        business = result.scalar_one_or_none()
        if not business:
            logger.warning(f"No business found for Stripe customer {stripe_customer_id}")
            return

        await db.execute(
            sa_update(Business)
            .where(Business.id == business.id)
            .values(subscription_status=status)
        )
        await db.commit()
        logger.info(f"Business {business.id} subscription → {status}")


async def _handle_payment_succeeded(event: dict):
    customer_id = event["data"]["object"].get("customer")
    if customer_id:
        await _update_subscription_status(customer_id, "active")


async def _handle_payment_failed(event: dict):
    customer_id = event["data"]["object"].get("customer")
    if customer_id:
        await _update_subscription_status(customer_id, "past_due")

        # Notify the business owner
        from app.models.business import Business
        async with async_session_factory() as db:
            result = await db.execute(
                select(Business).where(Business.stripe_customer_id == customer_id)
            )
            business = result.scalar_one_or_none()
            if business:
                from app.services.notifications import notify_owner
                await notify_owner(
                    business=business,
                    event="payment_failed",
                    data={"message": "Your payment failed. Please update your payment method to continue service."},
                )


async def _handle_subscription_deleted(event: dict):
    customer_id = event["data"]["object"].get("customer")
    if customer_id:
        await _update_subscription_status(customer_id, "canceled")


async def _handle_subscription_paused(event: dict):
    customer_id = event["data"]["object"].get("customer")
    if customer_id:
        await _update_subscription_status(customer_id, "paused")


async def _handle_subscription_resumed(event: dict):
    customer_id = event["data"]["object"].get("customer")
    if customer_id:
        await _update_subscription_status(customer_id, "active")
