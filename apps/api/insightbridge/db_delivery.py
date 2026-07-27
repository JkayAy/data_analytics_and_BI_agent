from __future__ import annotations

from typing import Any
from uuid import UUID

from insightbridge.crypto import decrypt_json, encrypt_json
from insightbridge.db import get_conn


def _encrypt_webhook(url: str) -> str:
    return encrypt_json({"webhook_url": url})


def _decrypt_webhook(blob: str) -> str:
    data = decrypt_json(blob)
    return str(data.get("webhook_url") or "")


def list_delivery_channels(org_id: str) -> list[dict[str, Any]]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
                SELECT id, org_id, name, channel_type, is_active, created_at
                FROM app.delivery_channels
                WHERE org_id = %s ORDER BY created_at ASC
                """,
            (org_id,),
        )
        out = []
        for row in cur.fetchall():
            item = dict(row)
            item["id"] = str(item["id"])
            item["org_id"] = str(item["org_id"])
            item["has_webhook"] = True
            if item.get("created_at"):
                item["created_at"] = item["created_at"].isoformat()
            out.append(item)
        return out


def create_delivery_channel(
    org_id: str,
    name: str,
    channel_type: str,
    webhook_url: str,
) -> dict[str, Any]:
    blob = _encrypt_webhook(webhook_url)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app.delivery_channels (org_id, name, channel_type, webhook_url_encrypted)
                VALUES (%s, %s, %s, %s)
                RETURNING id, org_id, name, channel_type, is_active, created_at
                """,
                (org_id, name, channel_type, blob),
            )
            row = dict(cur.fetchone())
            conn.commit()
    row["id"] = str(row["id"])
    row["org_id"] = str(row["org_id"])
    if row.get("created_at"):
        row["created_at"] = row["created_at"].isoformat()
    return row


def get_channel_webhook(channel_id: UUID | str, org_id: str) -> dict[str, Any] | None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
                SELECT id, org_id, name, channel_type, webhook_url_encrypted, is_active
                FROM app.delivery_channels
                WHERE id = %s AND org_id = %s
                """,
            (str(channel_id), org_id),
        )
        row = cur.fetchone()
        if not row:
            return None
        item = dict(row)
        item["id"] = str(item["id"])
        item["org_id"] = str(item["org_id"])
        item["webhook_url"] = _decrypt_webhook(item.pop("webhook_url_encrypted"))
        return item


def list_scheduled_reports(org_id: str) -> list[dict[str, Any]]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
                SELECT s.id, s.org_id, s.delivery_channel_id, s.name, s.question,
                       s.cron_expr, s.timezone, s.enabled, s.last_run_at, s.last_status,
                       s.last_error, s.created_at, c.name AS channel_name, c.channel_type
                FROM app.scheduled_reports s
                JOIN app.delivery_channels c ON c.id = s.delivery_channel_id
                WHERE s.org_id = %s
                ORDER BY s.created_at ASC
                """,
            (org_id,),
        )
        out = []
        for row in cur.fetchall():
            item = dict(row)
            for k in ("id", "org_id", "delivery_channel_id"):
                item[k] = str(item[k])
            for k in ("created_at", "last_run_at"):
                if item.get(k):
                    item[k] = item[k].isoformat()
            out.append(item)
        return out


def create_scheduled_report(
    org_id: str,
    delivery_channel_id: str,
    name: str,
    question: str,
    cron_expr: str,
    timezone: str,
    created_by: str | None,
    enabled: bool = True,
) -> dict[str, Any]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id FROM app.delivery_channels WHERE id = %s AND org_id = %s
                """,
                (delivery_channel_id, org_id),
            )
            if not cur.fetchone():
                raise ValueError("Delivery channel not found in organization")
            cur.execute(
                """
                INSERT INTO app.scheduled_reports (
                    org_id, delivery_channel_id, name, question, cron_expr, timezone, enabled, created_by
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, org_id, delivery_channel_id, name, question, cron_expr, timezone, enabled,
                          last_run_at, last_status, last_error, created_at
                """,
                (org_id, delivery_channel_id, name, question, cron_expr, timezone, enabled, created_by),
            )
            row = dict(cur.fetchone())
            conn.commit()
    for k in ("id", "org_id", "delivery_channel_id"):
        row[k] = str(row[k])
    if row.get("created_at"):
        row["created_at"] = row["created_at"].isoformat()
    return row


def set_schedule_enabled(schedule_id: UUID | str, org_id: str, enabled: bool) -> dict[str, Any] | None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
                UPDATE app.scheduled_reports
                SET enabled = %s
                WHERE id = %s AND org_id = %s
                RETURNING id, enabled
                """,
            (enabled, str(schedule_id), org_id),
        )
        row = cur.fetchone()
        conn.commit()
    if not row:
        return None
    return {"id": str(row["id"]), "enabled": row["enabled"]}


def list_enabled_schedules() -> list[dict[str, Any]]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
                SELECT s.id, s.org_id, s.delivery_channel_id, s.name, s.question,
                       s.cron_expr, s.timezone, s.last_run_at,
                       c.channel_type, c.webhook_url_encrypted, c.is_active AS channel_active
                FROM app.scheduled_reports s
                JOIN app.delivery_channels c ON c.id = s.delivery_channel_id
                WHERE s.enabled = true AND c.is_active = true
                """
        )
        out = []
        for row in cur.fetchall():
            item = dict(row)
            item["id"] = str(item["id"])
            item["org_id"] = str(item["org_id"])
            item["delivery_channel_id"] = str(item["delivery_channel_id"])
            item["webhook_url"] = _decrypt_webhook(item.pop("webhook_url_encrypted"))
            if item.get("last_run_at"):
                item["last_run_at"] = item["last_run_at"]
            out.append(item)
        return out


def mark_schedule_run(
    schedule_id: str,
    *,
    status: str,
    error: str | None = None,
) -> None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
                UPDATE app.scheduled_reports
                SET last_run_at = NOW(), last_status = %s, last_error = %s
                WHERE id = %s
                """,
            (status, error, schedule_id),
        )
        conn.commit()
