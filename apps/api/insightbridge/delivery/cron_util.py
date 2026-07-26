from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from croniter import croniter


def cron_due(cron_expr: str, timezone: str, last_run_at: datetime | None, now: datetime | None = None) -> bool:
    """True if a tick occurred since last_run_at (or never run and now matches schedule window)."""
    tz = ZoneInfo(timezone or "UTC")
    now = (now or datetime.now(tz)).astimezone(tz)
    if last_run_at is not None:
        if last_run_at.tzinfo is None:
            last_run_at = last_run_at.replace(tzinfo=ZoneInfo("UTC"))
        last = last_run_at.astimezone(tz)
    else:
        last = None

    itr = croniter(cron_expr, now)
    prev_tick = itr.get_prev(datetime)
    if last is None:
        # First run: fire if we are within 2 minutes after scheduled minute
        delta = (now - prev_tick).total_seconds()
        return 0 <= delta <= 120
    return prev_tick > last
