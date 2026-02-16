from celery.schedules import crontab

# Celery Beat schedule for periodic tasks
beat_schedule = {
    "compute-daily-metrics": {
        "task": "compute_daily_metrics",
        "schedule": crontab(hour=0, minute=5),  # Run at 12:05 AM UTC daily
    },
    "send-weekly-reports": {
        "task": "send_weekly_report",
        "schedule": crontab(hour=14, minute=0, day_of_week=1),  # Monday 10am ET
    },
}
