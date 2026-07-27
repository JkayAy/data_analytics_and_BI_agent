from __future__ import annotations

from datetime import UTC, date, datetime

from insightbridge.config import settings
from insightbridge.db import get_conn


def _period_month(d: date | None = None) -> date:
    d = d or datetime.now(UTC).date()
    return date(d.year, d.month, 1)


def get_org_usage(org_id: str) -> dict:
    period = _period_month()
    cap = settings.monthly_query_cap
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
                SELECT query_count FROM app.org_usage_monthly
                WHERE org_id = %s AND period_month = %s
                """,
            (org_id, period),
        )
        row = cur.fetchone()
        count = int(row["query_count"]) if row else 0
    return {
        "org_id": org_id,
        "period_month": period.isoformat(),
        "query_count": count,
        "monthly_cap": cap if cap > 0 else None,
        "remaining": (cap - count) if cap > 0 else None,
    }


def ensure_quota(org_id: str) -> None:
    cap = settings.monthly_query_cap
    if cap <= 0:
        return
    usage = get_org_usage(org_id)
    if usage["query_count"] >= cap:
        raise UsageQuotaExceeded(
            f"Monthly query cap reached ({cap}). Upgrade plan or wait until next period."
        )


class UsageQuotaExceeded(Exception):
    pass


def record_query_usage(org_id: str, *, amount: int = 1) -> dict:
    period = _period_month()
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
                INSERT INTO app.org_usage_monthly (org_id, period_month, query_count)
                VALUES (%s, %s, %s)
                ON CONFLICT (org_id, period_month)
                DO UPDATE SET
                    query_count = app.org_usage_monthly.query_count + EXCLUDED.query_count,
                    updated_at = NOW()
                RETURNING query_count
                """,
            (org_id, period, amount),
        )
        row = cur.fetchone()
        conn.commit()
    count = int(row["query_count"])
    cap = settings.monthly_query_cap
    return {
        "org_id": org_id,
        "period_month": period.isoformat(),
        "query_count": count,
        "monthly_cap": cap if cap > 0 else None,
        "remaining": (cap - count) if cap > 0 else None,
    }
