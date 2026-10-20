from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Alert, CheckResult, MonitoredService, User, utcnow
from app.redis_client import cache_get_json, cache_set_json
from app.schemas import DashboardSummary

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

CACHE_KEY = "dashboard:summary"
CACHE_TTL_SECONDS = 5


@router.get("/summary", response_model=DashboardSummary)
def summary(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    cached = cache_get_json(CACHE_KEY)
    if cached:
        return cached

    counts = dict(db.execute(select(MonitoredService.status, func.count()).group_by(MonitoredService.status)).all())
    active_alerts = db.scalar(select(func.count()).select_from(Alert).where(Alert.resolved_at.is_(None))) or 0

    now = utcnow()
    avg_ms = db.scalar(
        select(func.avg(CheckResult.response_ms)).where(
            CheckResult.checked_at >= now - timedelta(hours=1), CheckResult.is_up.is_(True)
        )
    )
    uptime = db.scalar(
        select(func.avg(case((CheckResult.is_up.is_(True), 1.0), else_=0.0))).where(
            CheckResult.checked_at >= now - timedelta(hours=24)
        )
    )
    data = {
        "total_services": sum(counts.values()),
        "up": counts.get("up", 0),
        "degraded": counts.get("degraded", 0),
        "down": counts.get("down", 0),
        "unknown": counts.get("unknown", 0),
        "active_alerts": active_alerts,
        "avg_response_ms_1h": round(float(avg_ms), 1) if avg_ms is not None else None,
        "uptime_24h": round(float(uptime) * 100, 2) if uptime is not None else None,
    }
    cache_set_json(CACHE_KEY, data, CACHE_TTL_SECONDS)
    return data
