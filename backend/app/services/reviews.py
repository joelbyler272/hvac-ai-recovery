import uuid


def get_google_review_link(place_id: str) -> str:
    """Generate a direct link to leave a Google review."""
    return f"https://search.google.com/local/writereview?placeid={place_id}"


async def send_review_request(
    business_id: uuid.UUID, lead_id: uuid.UUID, phone: str, review_url: str
) -> None:
    """Send a review request SMS after job completion."""
    # TODO: Implement review request via Celery delayed task (2hr delay)
    pass


async def send_review_reminder(review_request_id: uuid.UUID) -> None:
    """Send a single reminder if no review after 48 hours."""
    # TODO: Implement reminder via Celery
    pass
