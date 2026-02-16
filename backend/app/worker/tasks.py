from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "callrecover",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task(name="send_follow_up")
def send_follow_up(conversation_id: str):
    """Send a follow-up message to an unresponsive lead."""
    # TODO: Implement follow-up logic
    # 1. Check if conversation is still in follow_up status
    # 2. Check follow_up_count to determine which message to send
    # 3. Send appropriate follow-up SMS
    # 4. Schedule next follow-up or close conversation
    pass


@celery_app.task(name="send_review_request")
def send_review_request(review_request_id: str):
    """Send a review request SMS."""
    # TODO: Implement review request sending
    pass


@celery_app.task(name="compute_daily_metrics")
def compute_daily_metrics_task():
    """Compute daily metrics for all businesses."""
    # TODO: Iterate all businesses and compute metrics
    pass


@celery_app.task(name="send_weekly_report")
def send_weekly_report():
    """Generate and email weekly reports to all business owners."""
    # TODO: Implement weekly report generation
    pass
