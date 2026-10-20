from celery import Celery

from app.config import settings

celery_app = Celery(
    "cloudpulse",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.checks"],
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    task_time_limit=60,
    beat_schedule={
        "schedule-due-checks": {
            "task": "app.tasks.checks.schedule_due_checks",
            "schedule": float(settings.check_tick_seconds),
        }
    },
)
