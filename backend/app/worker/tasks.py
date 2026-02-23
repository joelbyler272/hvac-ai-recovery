import logging
from datetime import date, datetime, timedelta

from celery import Celery
from sqlalchemy import create_engine, select, update as sa_update
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.worker.schedules import beat_schedule

logger = logging.getLogger(__name__)
settings = get_settings()

celery_app = Celery(
    "callhook",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule=beat_schedule,
)

# Sync engine for Celery tasks (Celery doesn't support async)
_sync_engine = None
_SyncSession = None


def _get_sync_session() -> Session:
    global _sync_engine, _SyncSession
    if _sync_engine is None:
        sync_url = settings.database_url.replace(
            "postgresql+asyncpg://", "postgresql+psycopg2://"
        ).replace("postgresql://", "postgresql+psycopg2://")
        _sync_engine = create_engine(sync_url)
        _SyncSession = sessionmaker(bind=_sync_engine)
    return _SyncSession()


FOLLOW_UP_MESSAGES = [
    "Hey, just checking in! Did you still need help with your HVAC issue? We'd love to get you taken care of.",
    "Hi there! We haven't heard back from you. If you still need HVAC service, just reply and we'll get you scheduled.",
    "Last check-in! We're here whenever you're ready. Just reply to this message and we'll help you out. Have a great day!",
]


@celery_app.task(name="send_follow_up")
def send_follow_up(conversation_id: str):
    """Send a follow-up message to an unresponsive lead."""
    from app.models.conversation import Conversation
    from app.models.lead import Lead
    from app.models.business import Business

    session = _get_sync_session()
    try:
        convo = session.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.status.in_(["active", "follow_up"]),
            )
        ).scalar_one_or_none()

        if not convo:
            return

        business = session.execute(
            select(Business).where(Business.id == convo.business_id)
        ).scalar_one_or_none()

        if not business:
            return

        count = convo.follow_up_count or 0

        if count >= len(FOLLOW_UP_MESSAGES):
            session.execute(
                sa_update(Conversation)
                .where(Conversation.id == convo.id)
                .values(status="closed_unresponsive")
            )
            lead = session.execute(
                select(Lead).where(Lead.id == convo.lead_id)
            ).scalar_one_or_none()
            if lead and lead.status not in ("qualified", "booked"):
                session.execute(
                    sa_update(Lead)
                    .where(Lead.id == lead.id)
                    .values(status="unresponsive")
                )
            session.commit()
            return

        message_body = FOLLOW_UP_MESSAGES[count]

        try:
            from twilio.rest import Client

            client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
            lead = session.execute(
                select(Lead).where(Lead.id == convo.lead_id)
            ).scalar_one_or_none()

            if lead:
                client.messages.create(
                    to=lead.phone,
                    from_=business.twilio_number,
                    body=message_body,
                )

                from app.models.message import Message

                msg = Message(
                    conversation_id=convo.id,
                    business_id=business.id,
                    direction="outbound",
                    sender_type="ai",
                    body=message_body,
                )
                session.add(msg)
        except Exception as e:
            logger.warning(f"Failed to send follow-up SMS: {e}")

        session.execute(
            sa_update(Conversation)
            .where(Conversation.id == convo.id)
            .values(
                status="follow_up",
                follow_up_count=count + 1,
            )
        )
        session.commit()

        delays = [int(d) for d in settings.follow_up_delay_minutes.split(",")]
        if count < len(delays):
            celery_app.send_task(
                "send_follow_up",
                args=[conversation_id],
                countdown=delays[count] * 60,
            )
    except Exception as e:
        logger.error(f"Follow-up task failed: {e}")
        session.rollback()
    finally:
        session.close()


@celery_app.task(name="send_review_request")
def send_review_request(review_request_id: str):
    """Send a review request SMS."""
    from app.models.review_request import ReviewRequest
    from app.models.business import Business
    from app.models.lead import Lead

    session = _get_sync_session()
    try:
        rr = session.execute(
            select(ReviewRequest).where(ReviewRequest.id == review_request_id)
        ).scalar_one_or_none()

        if not rr or rr.status != "pending":
            return

        business = session.execute(
            select(Business).where(Business.id == rr.business_id)
        ).scalar_one_or_none()

        lead = session.execute(
            select(Lead).where(Lead.id == rr.lead_id)
        ).scalar_one_or_none()

        if not business or not lead:
            return

        try:
            from twilio.rest import Client

            client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
            name = lead.name or "there"
            msg = (
                f"Hi {name}! Thanks for choosing {business.name}. "
                f"We'd love to hear how we did. Could you leave us a quick review? "
                f"It really helps! Thanks!"
            )
            client.messages.create(
                to=lead.phone, from_=business.twilio_number, body=msg
            )

            session.execute(
                sa_update(ReviewRequest)
                .where(ReviewRequest.id == rr.id)
                .values(status="sent", sent_at=datetime.utcnow())
            )
            session.commit()

            celery_app.send_task(
                "send_review_reminder",
                args=[review_request_id],
                countdown=48 * 3600,
            )
        except Exception as e:
            logger.warning(f"Failed to send review SMS: {e}")
            session.execute(
                sa_update(ReviewRequest)
                .where(ReviewRequest.id == rr.id)
                .values(status="failed")
            )
            session.commit()
    except Exception as e:
        logger.error(f"Review request task failed: {e}")
        session.rollback()
    finally:
        session.close()


@celery_app.task(name="send_review_reminder")
def send_review_reminder(review_request_id: str):
    """Send a reminder for the review request."""
    from app.models.review_request import ReviewRequest
    from app.models.business import Business
    from app.models.lead import Lead

    session = _get_sync_session()
    try:
        rr = session.execute(
            select(ReviewRequest).where(ReviewRequest.id == review_request_id)
        ).scalar_one_or_none()

        if not rr or rr.status != "sent":
            return

        business = session.execute(
            select(Business).where(Business.id == rr.business_id)
        ).scalar_one_or_none()
        lead = session.execute(
            select(Lead).where(Lead.id == rr.lead_id)
        ).scalar_one_or_none()

        if not business or not lead:
            return

        try:
            from twilio.rest import Client

            client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
            msg = (
                f"Just a friendly reminder from {business.name} - "
                f"we'd really appreciate a quick review when you get a chance. Thanks!"
            )
            client.messages.create(
                to=lead.phone, from_=business.twilio_number, body=msg
            )
            session.execute(
                sa_update(ReviewRequest)
                .where(ReviewRequest.id == rr.id)
                .values(status="reminded")
            )
            session.commit()
        except Exception as e:
            logger.warning(f"Failed to send review reminder: {e}")
    except Exception as e:
        logger.error(f"Review reminder task failed: {e}")
        session.rollback()
    finally:
        session.close()


@celery_app.task(name="compute_daily_metrics")
def compute_daily_metrics_task():
    """Compute daily metrics for all businesses."""
    from app.models.business import Business

    session = _get_sync_session()
    try:
        businesses = session.execute(
            select(Business).where(Business.subscription_status == "active")
        ).scalars().all()

        yesterday = date.today() - timedelta(days=1)

        for biz in businesses:
            try:
                _compute_metrics_for_business(session, biz.id, yesterday)
            except Exception as e:
                logger.warning(f"Failed metrics for {biz.id}: {e}")

        session.commit()
    except Exception as e:
        logger.error(f"Daily metrics task failed: {e}")
        session.rollback()
    finally:
        session.close()


def _compute_metrics_for_business(session: Session, business_id, for_date: date):
    """Compute and upsert daily metrics for a single business."""
    from sqlalchemy import func
    from app.models.call import Call
    from app.models.lead import Lead
    from app.models.conversation import Conversation
    from app.models.appointment import Appointment
    from app.models.daily_metric import DailyMetric

    day_start = datetime.combine(for_date, datetime.min.time())
    day_end = datetime.combine(for_date + timedelta(days=1), datetime.min.time())

    total_calls = session.execute(
        select(func.count(Call.id)).where(
            Call.business_id == business_id,
            Call.created_at >= day_start,
            Call.created_at < day_end,
        )
    ).scalar() or 0

    missed_calls = session.execute(
        select(func.count(Call.id)).where(
            Call.business_id == business_id,
            Call.status == "missed",
            Call.created_at >= day_start,
            Call.created_at < day_end,
        )
    ).scalar() or 0

    recovered = session.execute(
        select(func.count(Conversation.id)).where(
            Conversation.business_id == business_id,
            Conversation.status.in_(["active", "qualified", "human_active"]),
            Conversation.created_at >= day_start,
            Conversation.created_at < day_end,
        )
    ).scalar() or 0

    leads_captured = session.execute(
        select(func.count(Lead.id)).where(
            Lead.business_id == business_id,
            Lead.created_at >= day_start,
            Lead.created_at < day_end,
        )
    ).scalar() or 0

    leads_qualified = session.execute(
        select(func.count(Lead.id)).where(
            Lead.business_id == business_id,
            Lead.status == "qualified",
            Lead.created_at >= day_start,
            Lead.created_at < day_end,
        )
    ).scalar() or 0

    appts = session.execute(
        select(func.count(Appointment.id)).where(
            Appointment.business_id == business_id,
            Appointment.created_at >= day_start,
            Appointment.created_at < day_end,
        )
    ).scalar() or 0

    revenue = session.execute(
        select(func.coalesce(func.sum(Lead.estimated_value), 0)).where(
            Lead.business_id == business_id,
            Lead.status.in_(["qualified", "booked"]),
            Lead.created_at >= day_start,
            Lead.created_at < day_end,
        )
    ).scalar() or 0

    existing = session.execute(
        select(DailyMetric).where(
            DailyMetric.business_id == business_id,
            DailyMetric.date == for_date,
        )
    ).scalar_one_or_none()

    if existing:
        session.execute(
            sa_update(DailyMetric)
            .where(DailyMetric.id == existing.id)
            .values(
                total_calls=total_calls,
                missed_calls=missed_calls,
                recovered_calls=recovered,
                leads_captured=leads_captured,
                leads_qualified=leads_qualified,
                appointments_booked=appts,
                estimated_revenue=revenue,
            )
        )
    else:
        metric = DailyMetric(
            business_id=business_id,
            date=for_date,
            total_calls=total_calls,
            missed_calls=missed_calls,
            recovered_calls=recovered,
            leads_captured=leads_captured,
            leads_qualified=leads_qualified,
            appointments_booked=appts,
            estimated_revenue=revenue,
        )
        session.add(metric)


@celery_app.task(name="send_weekly_report")
def send_weekly_report():
    """Generate and email weekly reports to all business owners."""
    from app.models.business import Business
    from app.models.daily_metric import DailyMetric

    if not settings.resend_api_key:
        logger.info("Resend not configured, skipping weekly report.")
        return

    session = _get_sync_session()
    try:
        import resend

        resend.api_key = settings.resend_api_key

        businesses = session.execute(
            select(Business).where(Business.subscription_status == "active")
        ).scalars().all()

        week_start = date.today() - timedelta(days=7)

        for biz in businesses:
            try:
                metrics = session.execute(
                    select(DailyMetric).where(
                        DailyMetric.business_id == biz.id,
                        DailyMetric.date >= week_start,
                        DailyMetric.date <= date.today(),
                    )
                ).scalars().all()

                total_calls = sum(m.total_calls for m in metrics)
                missed = sum(m.missed_calls for m in metrics)
                recovered = sum(m.recovered_calls for m in metrics)
                leads = sum(m.leads_captured for m in metrics)
                qualified = sum(m.leads_qualified for m in metrics)
                appts = sum(m.appointments_booked for m in metrics)
                revenue = sum(float(m.estimated_revenue) for m in metrics)

                body = (
                    f"Weekly Report for {biz.name}\n"
                    f"Period: {week_start} - {date.today()}\n\n"
                    f"Total Calls: {total_calls}\n"
                    f"Missed Calls: {missed}\n"
                    f"Recovered: {recovered}\n"
                    f"Leads Captured: {leads}\n"
                    f"Leads Qualified: {qualified}\n"
                    f"Appointments Booked: {appts}\n"
                    f"Estimated Revenue: ${revenue:,.2f}\n"
                )

                resend.Emails.send({
                    "from": settings.email_from_address,
                    "to": biz.owner_email,
                    "subject": f"CallHook Weekly Report - {biz.name}",
                    "text": body,
                })
            except Exception as e:
                logger.warning(f"Failed weekly report for {biz.id}: {e}")

    except Exception as e:
        logger.error(f"Weekly report task failed: {e}")
    finally:
        session.close()
