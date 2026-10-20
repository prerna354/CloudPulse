import logging
import time
from dataclasses import dataclass

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Alert, CheckResult, MonitoredService, utcnow
from app.redis_client import publish_event
from app.services.status_logic import (
    OPEN_CRITICAL,
    OPEN_WARNING,
    RESOLVE,
    compute_status,
    decide_alert_action,
)

logger = logging.getLogger(__name__)


@dataclass
class ProbeResult:
    is_up: bool
    status_code: int | None
    response_ms: int
    error: str | None


def probe_url(url: str, timeout_ms: int) -> ProbeResult:
    started = time.perf_counter()
    try:
        response = httpx.get(url, timeout=timeout_ms / 1000, follow_redirects=True)
        elapsed = int((time.perf_counter() - started) * 1000)
        ok = response.status_code < 400
        return ProbeResult(ok, response.status_code, elapsed, None if ok else f"HTTP {response.status_code}")
    except httpx.TimeoutException:
        return ProbeResult(False, None, timeout_ms, "Request timed out")
    except httpx.HTTPError as exc:
        elapsed = int((time.perf_counter() - started) * 1000)
        return ProbeResult(False, None, elapsed, (str(exc) or type(exc).__name__)[:200])


def record_result(db: Session, service: MonitoredService, probe: ProbeResult) -> str:
    """Store a check, update service status, manage alerts, and publish events."""
    previous_status = service.status
    now = utcnow()

    service.consecutive_failures = 0 if probe.is_up else service.consecutive_failures + 1
    new_status = compute_status(probe.is_up, probe.response_ms, service.consecutive_failures)

    db.add(
        CheckResult(
            service_id=service.id,
            checked_at=now,
            is_up=probe.is_up,
            status_code=probe.status_code,
            response_ms=probe.response_ms,
            error=probe.error,
        )
    )

    service.status = new_status
    service.last_checked_at = now
    service.last_response_ms = probe.response_ms

    events: list[dict] = [
        {
            "type": "check",
            "service_id": service.id,
            "service_name": service.name,
            "status": new_status,
            "response_ms": probe.response_ms,
            "checked_at": now.isoformat(),
        }
    ]

    action = decide_alert_action(previous_status, new_status)

    if action in (OPEN_CRITICAL, OPEN_WARNING):
        severity = "critical" if action == OPEN_CRITICAL else "warning"
        reason = probe.error or f"response took {probe.response_ms} ms"

        if action == OPEN_CRITICAL:
            message = (
                f"{service.name} is down after "
                f"{service.consecutive_failures} failed checks ({reason})"
            )
        else:
            message = f"{service.name} is degraded ({reason})"

        open_alerts = db.scalars(
            select(Alert)
            .where(
                Alert.service_id == service.id,
                Alert.resolved_at.is_(None),
            )
            .order_by(Alert.created_at.asc(), Alert.id.asc())
        ).all()

        if open_alerts:
            alert = open_alerts[0]

            if action == OPEN_CRITICAL and alert.severity != "critical":
                alert.severity = "critical"
                alert.message = message
                alert.acknowledged = False

                events.append(
                    {
                        "type": "alert",
                        "action": "escalated",
                        "severity": "critical",
                        "service_name": service.name,
                        "message": message,
                    }
                )
            elif action == OPEN_CRITICAL:
                alert.message = message
        else:
            db.add(
                Alert(
                    service_id=service.id,
                    severity=severity,
                    message=message,
                    created_at=now,
                )
            )

            events.append(
                {
                    "type": "alert",
                    "action": "opened",
                    "severity": severity,
                    "service_name": service.name,
                    "message": message,
                }
            )

    elif action == RESOLVE:
        open_alerts = db.scalars(
            select(Alert).where(
                Alert.service_id == service.id,
                Alert.resolved_at.is_(None),
            )
        ).all()

        for alert in open_alerts:
            alert.resolved_at = now

        if open_alerts:
            events.append(
                {
                    "type": "alert",
                    "action": "resolved",
                    "severity": "info",
                    "service_name": service.name,
                    "message": f"{service.name} has recovered",
                }
            )

    db.commit()

    for event in events:
        publish_event(event)

    return new_status
