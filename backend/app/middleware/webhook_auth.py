"""Webhook signature validation for Twilio and Vapi."""

import hashlib
import hmac
import logging

from fastapi import Request, HTTPException

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def verify_twilio_signature(request: Request) -> None:
    """
    Validate Twilio webhook signature.

    Uses X-Twilio-Signature header to verify the request came from Twilio.
    Skips validation in development if auth token is not configured.
    """
    if not settings.twilio_auth_token:
        return  # Skip in dev

    signature = request.headers.get("X-Twilio-Signature", "")
    if not signature:
        if settings.environment == "development":
            return
        raise HTTPException(status_code=403, detail="Missing Twilio signature")

    try:
        from twilio.request_validator import RequestValidator

        validator = RequestValidator(settings.twilio_auth_token)
        url = str(request.url)
        form = await request.form()
        params = dict(form)

        if not validator.validate(url, params, signature):
            raise HTTPException(status_code=403, detail="Invalid Twilio signature")
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Twilio signature validation error: {e}")
        if settings.environment != "development":
            raise HTTPException(status_code=403, detail="Signature validation failed")


async def verify_vapi_signature(request: Request) -> None:
    """
    Validate Vapi webhook signature using HMAC-SHA256.

    Skips validation if webhook secret is not configured.
    """
    if not settings.vapi_webhook_secret:
        return  # Skip if not configured

    signature = request.headers.get("x-vapi-signature", "")
    if not signature:
        if settings.environment == "development":
            return
        raise HTTPException(status_code=403, detail="Missing Vapi signature")

    body = await request.body()
    expected = hmac.new(
        settings.vapi_webhook_secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=403, detail="Invalid Vapi signature")
