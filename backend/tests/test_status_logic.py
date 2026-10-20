import unittest

from app.services.status_logic import (
    OPEN_CRITICAL,
    OPEN_WARNING,
    RESOLVE,
    compute_status,
    decide_alert_action,
    uptime_percentage,
)


class ComputeStatusTests(unittest.TestCase):
    def test_fast_successful_check_is_up(self):
        self.assertEqual(compute_status(True, 120, 0), "up")

    def test_slow_successful_check_is_degraded(self):
        self.assertEqual(compute_status(True, 1500, 0), "degraded")

    def test_single_failure_is_degraded_not_down(self):
        self.assertEqual(compute_status(False, 5000, 1), "degraded")

    def test_three_failures_in_a_row_is_down(self):
        self.assertEqual(compute_status(False, 5000, 3), "down")


class AlertDecisionTests(unittest.TestCase):
    def test_going_down_opens_critical_alert(self):
        self.assertEqual(decide_alert_action("degraded", "down"), OPEN_CRITICAL)

    def test_going_degraded_from_up_opens_warning(self):
        self.assertEqual(decide_alert_action("up", "degraded"), OPEN_WARNING)

    def test_recovery_resolves_alerts(self):
        self.assertEqual(decide_alert_action("down", "up"), RESOLVE)

    def test_no_change_does_nothing(self):
        self.assertIsNone(decide_alert_action("up", "up"))
        self.assertIsNone(decide_alert_action("down", "down"))


class UptimeTests(unittest.TestCase):
    def test_percentage(self):
        self.assertEqual(uptime_percentage([True, True, True, False]), 75.0)

    def test_no_data_returns_none(self):
        self.assertIsNone(uptime_percentage([]))


if __name__ == "__main__":
    unittest.main()
