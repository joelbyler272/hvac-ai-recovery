import uuid
import logging

import redis as redis_lib

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _get_redis():
    return redis_lib.from_url(settings.redis_url)


async def schedule_follow_up(
    conversation_id: uuid.UUID, delay_minutes: int
) -> str | None:
    """Schedule a follow-up message and return the Celery task ID."""
    try:
        from app.worker.tasks import celery_app

        result = celery_app.send_task(
            "send_follow_up",
            args=[str(conversation_id)],
            countdown=delay_minutes * 60,
        )

        # Store task ID in Redis for cancellation
        try:
            r = _get_redis()
            r.set(
                f"followup:{conversation_id}",
                result.id,
                ex=delay_minutes * 60 + 300,
            )
        except Exception as e:
            logger.warning(f"Failed to store follow-up task ID in Redis: {e}")

        return result.id
    except Exception as e:
        logger.warning(f"Failed to schedule follow-up: {e}")
        return None


async def cancel_pending_follow_ups(conversation_id: uuid.UUID) -> None:
    """Cancel any pending follow-up tasks for a conversation."""
    try:
        from app.worker.tasks import celery_app

        r = _get_redis()
        task_id = r.get(f"followup:{conversation_id}")
        if task_id:
            celery_app.control.revoke(task_id.decode(), terminate=False)
            r.delete(f"followup:{conversation_id}")
    except Exception as e:
        logger.warning(f"Failed to cancel follow-up: {e}")
