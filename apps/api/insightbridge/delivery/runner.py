from __future__ import annotations

import logging

from insightbridge.agent import run_agent
from insightbridge.db_delivery import get_channel_webhook, list_enabled_schedules, mark_schedule_run
from insightbridge.delivery.cron_util import cron_due
from insightbridge.delivery.formatters import format_slack_payload, format_teams_payload
from insightbridge.delivery.webhook_client import WebhookDeliveryError, post_json
from insightbridge.usage import UsageQuotaExceeded, ensure_quota, record_query_usage

logger = logging.getLogger(__name__)


def deliver_agent_result(
    channel_type: str,
    webhook_url: str,
    result,
    *,
    title: str,
    question: str,
) -> None:
    if channel_type == "teams":
        payload = format_teams_payload(result, title=title, question=question)
    else:
        payload = format_slack_payload(result, title=title, question=question)
    post_json(webhook_url, payload)


def run_due_scheduled_reports() -> list[dict]:
    """Run all due schedules; returns summary rows for logging."""
    summaries: list[dict] = []
    for sched in list_enabled_schedules():
        sid = sched["id"]
        try:
            if not cron_due(sched["cron_expr"], sched["timezone"], sched.get("last_run_at")):
                continue
            org_id = sched["org_id"]
            ensure_quota(org_id)
            result = run_agent(sched["question"])
            record_query_usage(org_id)
            url = sched.get("webhook_url") or ""
            if not url:
                ch = get_channel_webhook(sched["delivery_channel_id"], org_id)
                url = (ch or {}).get("webhook_url") or ""
            deliver_agent_result(
                sched["channel_type"],
                url,
                result,
                title=sched["name"],
                question=sched["question"],
            )
            mark_schedule_run(sid, status=result.status, error=result.error)
            summaries.append({"schedule_id": sid, "status": result.status})
        except UsageQuotaExceeded as exc:
            mark_schedule_run(sid, status="quota_exceeded", error=str(exc))
            summaries.append({"schedule_id": sid, "status": "quota_exceeded"})
        except WebhookDeliveryError as exc:
            mark_schedule_run(sid, status="delivery_failed", error=str(exc))
            summaries.append({"schedule_id": sid, "status": "delivery_failed"})
        except Exception as exc:
            logger.exception("Scheduled report %s failed", sid)
            mark_schedule_run(sid, status="failed", error=str(exc))
            summaries.append({"schedule_id": sid, "status": "failed"})
    return summaries
