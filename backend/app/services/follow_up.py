import uuid


async def schedule_follow_up(conversation_id: uuid.UUID, delay_minutes: int) -> None:
    """Schedule a follow-up message if no reply within delay_minutes."""
    # TODO: Implement via Celery delayed task
    # celery_app.send_task(
    #     'app.worker.tasks.send_follow_up',
    #     args=[str(conversation_id)],
    #     countdown=delay_minutes * 60
    # )
    pass


async def cancel_pending_follow_ups(conversation_id: uuid.UUID) -> None:
    """Cancel any pending follow-up tasks for a conversation."""
    # TODO: Implement Celery task revocation
    pass
