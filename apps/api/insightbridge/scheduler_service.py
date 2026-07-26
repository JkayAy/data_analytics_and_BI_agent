from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from insightbridge.config import settings
from insightbridge.delivery.runner import run_due_scheduled_reports

logger = logging.getLogger(__name__)
_scheduler: BackgroundScheduler | None = None


def _tick() -> None:
    try:
        ran = run_due_scheduled_reports()
        if ran:
            logger.info("Scheduled reports executed: %s", ran)
    except Exception:
        logger.exception("Scheduler tick failed")


def start_scheduler() -> BackgroundScheduler | None:
    global _scheduler
    if not settings.scheduler_enabled:
        return None
    if _scheduler is not None:
        return _scheduler
    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(
        _tick,
        "interval",
        seconds=settings.scheduler_poll_seconds,
        id="insightbridge_scheduled_reports",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("E6 scheduler started (every %ss)", settings.scheduler_poll_seconds)
    return _scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
