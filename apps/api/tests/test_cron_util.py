from datetime import datetime
from zoneinfo import ZoneInfo

from insightbridge.delivery.cron_util import cron_due


def test_cron_due_after_last_run():
    tz = ZoneInfo("UTC")
    # Every minute at second 0 — use a fixed Monday 9:00
    last = datetime(2026, 1, 5, 8, 59, tzinfo=tz)  # Monday
    now = datetime(2026, 1, 5, 9, 0, 30, tzinfo=tz)
    assert cron_due("0 9 * * 1", "UTC", last, now) is True


def test_cron_not_due_same_window():
    tz = ZoneInfo("UTC")
    last = datetime(2026, 1, 5, 9, 1, tzinfo=tz)
    now = datetime(2026, 1, 5, 9, 2, tzinfo=tz)
    assert cron_due("0 9 * * 1", "UTC", last, now) is False
