"""Create tables and load realistic demo data. Safe to run more than once."""
import logging
import random
from datetime import timedelta

from sqlalchemy import select

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import Alert, CheckResult, MonitoredService, User, utcnow
from app.security import hash_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")


def demo_services() -> list[tuple[str, str, str]]:
    base = settings.demo_base_url.rstrip("/")
    return [
        ("Payments API", f"{base}/api/demo/ok", "up"),
        ("Auth Service", f"{base}/api/demo/ok", "up"),
        ("Search Service", f"{base}/api/demo/slow", "degraded"),
        ("Notification Worker", f"{base}/api/demo/flaky", "flaky"),
        ("Legacy Reporting", f"{base}/api/demo/down", "down"),
        ("Public Website", "https://www.python.org", "up"),
    ]


def seed() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if db.scalar(select(User).limit(1)):
            logger.info("Database already seeded; nothing to do")
            return
        if not settings.seed_admin_password or not settings.seed_viewer_password:
            raise SystemExit("Set SEED_ADMIN_PASSWORD and SEED_VIEWER_PASSWORD in your .env file first.")

        db.add_all([
            User(email="admin@cloudpulse.dev", full_name="Ananya Deshmukh", role="admin",
                 hashed_password=hash_password(settings.seed_admin_password)),
            User(email="viewer@cloudpulse.dev", full_name="Rohan Kulkarni", role="viewer",
                 hashed_password=hash_password(settings.seed_viewer_password)),
        ])

        rng = random.Random(42)
        now = utcnow()
        for name, url, profile in demo_services():
            service = MonitoredService(name=name, url=url, check_interval_seconds=30)
            db.add(service)
            db.flush()
            for i in range(96):  # 24 hours of history, one point every 15 minutes
                when = now - timedelta(minutes=15 * (95 - i))
                if profile == "down":
                    up, ms = False, 5000
                elif profile == "degraded":
                    up, ms = True, rng.randint(1100, 1700)
                elif profile == "flaky":
                    up = rng.random() > 0.3
                    ms = rng.randint(80, 400) if up else 5000
                else:
                    up, ms = True, rng.randint(60, 320)
                db.add(CheckResult(service_id=service.id, checked_at=when, is_up=up,
                                   status_code=200 if up else 503, response_ms=ms,
                                   error=None if up else "HTTP 503"))
            service.status = "unknown" if profile == "flaky" else ("up" if profile == "up" else profile)
            service.last_checked_at = now
            service.last_response_ms = 5000 if profile == "down" else None
            if profile == "down":
                service.consecutive_failures = 3
                db.add(Alert(service_id=service.id, severity="critical", created_at=now - timedelta(hours=3),
                             message=f"{name} is down after 3 failed checks (HTTP 503)"))
            if profile == "degraded":
                db.add(Alert(service_id=service.id, severity="warning", created_at=now - timedelta(hours=1),
                             message=f"{name} is degraded (response took 1320 ms)"))
        db.commit()
        logger.info("Seeded demo users, services, history and alerts")


if __name__ == "__main__":
    seed()
