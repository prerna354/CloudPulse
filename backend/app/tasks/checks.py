import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.database import SessionLocal
from app.models import MonitoredService, utcnow
from app.services.monitoring import probe_url, record_result
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _as_utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


@celery_app.task(name="app.tasks.checks.schedule_due_checks")
def schedule_due_checks() -> int:
    """Runs on a timer (Celery beat). Queues a check for every service that is due."""
    now = utcnow()
    queued = 0
    with SessionLocal() as db:
        services = db.scalars(select(MonitoredService).where(MonitoredService.is_active.is_(True))).all()
        for service in services:
            due = service.last_checked_at is None or (
                (now - _as_utc(service.last_checked_at)).total_seconds() >= service.check_interval_seconds
            )
            if due:
                run_check.delay(service.id)
                queued += 1
    return queued


@celery_app.task(name="app.tasks.checks.run_check")
def run_check(service_id: int) -> str | None:
    """Probe one service and store the outcome. Many of these run in parallel on workers."""
    with SessionLocal() as db:
        service = db.get(MonitoredService, service_id)
        if service is None or not service.is_active:
            return None
        probe = probe_url(service.url, service.timeout_ms)
        status = record_result(db, service, probe)
        logger.info("Checked %s -> %s (%d ms)", service.name, status, probe.response_ms)
        return status
