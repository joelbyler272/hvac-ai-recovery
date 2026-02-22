import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review_request import ReviewRequest


def get_google_review_link(place_id: str) -> str:
    """Generate a direct link to leave a Google review."""
    return f"https://search.google.com/local/writereview?placeid={place_id}"


async def create_review_request(
    db: AsyncSession,
    business_id: uuid.UUID,
    lead_id: uuid.UUID,
    phone: str,
    review_url: str,
) -> ReviewRequest:
    """Create a review request record and schedule sending."""
    rr = ReviewRequest(
        business_id=business_id,
        lead_id=lead_id,
        phone=phone,
        review_url=review_url,
        status="pending",
    )
    db.add(rr)
    await db.flush()

    # Schedule Celery task to send in 2 hours
    try:
        from app.worker.tasks import celery_app

        celery_app.send_task(
            "send_review_request",
            args=[str(rr.id)],
            countdown=2 * 60 * 60,
        )
    except Exception:
        pass  # Celery may not be running in dev

    return rr
