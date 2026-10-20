"""Pure decision logic (no I/O) so it is easy to unit test."""

SLOW_THRESHOLD_MS = 1000
FAILURE_THRESHOLD = 3

OPEN_CRITICAL = "open_critical"
OPEN_WARNING = "open_warning"
RESOLVE = "resolve"


def compute_status(
    is_up: bool,
    response_ms: int,
    consecutive_failures: int,
    slow_ms: int = SLOW_THRESHOLD_MS,
    failure_threshold: int = FAILURE_THRESHOLD,
) -> str:
    """Return 'up', 'degraded' or 'down' for the latest check.

    A single failed check only marks the service degraded; it is declared
    down after `failure_threshold` failures in a row. This avoids false alarms
    from one dropped request.
    """
    if not is_up:
        return "down" if consecutive_failures >= failure_threshold else "degraded"
    if response_ms > slow_ms:
        return "degraded"
    return "up"


def decide_alert_action(previous_status: str, new_status: str) -> str | None:
    """Decide whether a status change should open or resolve alerts."""
    if new_status == previous_status:
        return None
    if new_status == "down":
        return OPEN_CRITICAL
    if new_status == "degraded" and previous_status in ("up", "unknown"):
        return OPEN_WARNING
    if new_status == "up" and previous_status in ("down", "degraded"):
        return RESOLVE
    return None


def uptime_percentage(check_outcomes: list[bool]) -> float | None:
    if not check_outcomes:
        return None
    return round(100 * sum(check_outcomes) / len(check_outcomes), 2)
