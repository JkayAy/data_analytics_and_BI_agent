from __future__ import annotations

import hashlib
import hmac
import time
from urllib.parse import parse_qs

from insightbridge.agent import run_agent
from insightbridge.config import settings
from insightbridge.delivery.formatters import format_slack_ephemeral
from insightbridge.usage import UsageQuotaExceeded, ensure_quota, record_query_usage


class SlackSignatureError(Exception):
    pass


def verify_slack_signature(body: bytes, timestamp: str, signature: str) -> None:
    secret = settings.slack_signing_secret
    if not secret:
        raise SlackSignatureError("SLACK_SIGNING_SECRET not configured")
    if abs(time.time() - int(timestamp)) > 60 * 5:
        raise SlackSignatureError("Request timestamp too old")
    base = f"v0:{timestamp}:{body.decode('utf-8')}"
    digest = hmac.new(secret.encode(), base.encode(), hashlib.sha256).hexdigest()
    expected = f"v0={digest}"
    if not hmac.compare_digest(expected, signature):
        raise SlackSignatureError("Invalid signature")


def parse_slash_command(body: bytes) -> dict[str, str]:
    data = parse_qs(body.decode("utf-8"))
    return {k: (v[0] if v else "") for k, v in data.items()}


def handle_slash_command(text: str, org_id: str | None = None) -> dict:
    org_id = org_id or settings.default_org_id
    question = (text or "").strip() or "What is our total MRR?"
    ensure_quota(org_id)
    result = run_agent(question)
    record_query_usage(org_id)
    return format_slack_ephemeral(result, question)
