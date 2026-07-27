from __future__ import annotations

import json
from typing import Any
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from insightbridge.config import settings


def get_conn():
    return psycopg.connect(settings.database_url, row_factory=dict_row)


def create_conversation(
    title: str | None = None,
    *,
    org_id: str | None = None,
    created_by: str | None = None,
) -> dict[str, Any]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
                INSERT INTO app.conversations (title, org_id, created_by)
                VALUES (%s, %s, %s)
                RETURNING id, title, org_id, created_at
                """,
            (title, org_id, created_by),
        )
        row = cur.fetchone()
        conn.commit()
        out = dict(row)
        out["id"] = str(out["id"])
        if out.get("org_id"):
            out["org_id"] = str(out["org_id"])
        return out


def get_conversation_org(conversation_id: UUID) -> str | None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT org_id FROM app.conversations WHERE id = %s",
            (str(conversation_id),),
        )
        row = cur.fetchone()
        if not row or not row["org_id"]:
            return None
        return str(row["org_id"])


def add_message(conversation_id: UUID, role: str, content: dict[str, Any]) -> dict[str, Any]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
                INSERT INTO app.messages (conversation_id, role, content)
                VALUES (%s, %s, %s::jsonb)
                RETURNING id, conversation_id, role, content, created_at
                """,
            (str(conversation_id), role, json.dumps(content)),
        )
        row = cur.fetchone()
        conn.commit()
        return _serialize_message(dict(row))


def save_query_run(
    message_id: UUID | None,
    *,
    question_text: str | None,
    sql_text: str,
    status: str,
    row_count: int | None,
    duration_ms: int | None,
    error_message: str | None,
    result_preview: list[dict[str, Any]] | None,
    chart_spec: dict[str, Any] | None,
    run_metadata: dict[str, Any] | None = None,
    org_id: str | None = None,
) -> dict[str, Any]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
                INSERT INTO app.query_runs
                  (message_id, question_text, sql_text, status, row_count, duration_ms,
                   error_message, result_preview, chart_spec, run_metadata, org_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s)
                RETURNING id, created_at
                """,
            (
                str(message_id) if message_id else None,
                question_text,
                sql_text,
                status,
                row_count,
                duration_ms,
                error_message,
                json.dumps(result_preview) if result_preview is not None else None,
                json.dumps(chart_spec) if chart_spec else None,
                json.dumps(run_metadata) if run_metadata else None,
                org_id,
            ),
        )
        row = cur.fetchone()
        conn.commit()
        out = dict(row)
        out["id"] = str(out["id"])
        if out.get("created_at"):
            out["created_at"] = out["created_at"].isoformat()
        return out


def list_query_runs(*, limit: int = 50, org_id: str | None = None) -> list[dict[str, Any]]:
    with get_conn() as conn, conn.cursor() as cur:
        if org_id:
            cur.execute(
                """
                    SELECT qr.id, qr.question_text, qr.sql_text, qr.status, qr.row_count,
                           qr.duration_ms, qr.error_message, qr.created_at,
                           f.rating AS feedback_rating
                    FROM app.query_runs qr
                    LEFT JOIN app.feedback f ON f.query_run_id = qr.id
                    WHERE qr.org_id = %s
                    ORDER BY qr.created_at DESC
                    LIMIT %s
                    """,
                (org_id, limit),
            )
        else:
            cur.execute(
                """
                    SELECT qr.id, qr.question_text, qr.sql_text, qr.status, qr.row_count,
                           qr.duration_ms, qr.error_message, qr.created_at,
                           f.rating AS feedback_rating
                    FROM app.query_runs qr
                    LEFT JOIN app.feedback f ON f.query_run_id = qr.id
                    ORDER BY qr.created_at DESC
                    LIMIT %s
                    """,
                (limit,),
            )
        rows = []
        for r in cur.fetchall():
            item = dict(r)
            item["id"] = str(item["id"])
            if item.get("created_at"):
                item["created_at"] = item["created_at"].isoformat()
            rows.append(item)
        return rows


def list_query_runs_for_org(org_id: str, *, limit: int = 5000) -> list[dict[str, Any]]:
    return list_query_runs(limit=limit, org_id=org_id)


def upsert_feedback(query_run_id: UUID, rating: int, comment: str | None = None) -> dict[str, Any]:
    if rating not in (-1, 1):
        raise ValueError("rating must be -1 or 1")
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
                INSERT INTO app.feedback (query_run_id, rating, comment)
                VALUES (%s, %s, %s)
                ON CONFLICT (query_run_id) DO UPDATE
                  SET rating = EXCLUDED.rating,
                      comment = COALESCE(EXCLUDED.comment, app.feedback.comment)
                RETURNING id, query_run_id, rating, comment, created_at
                """,
            (str(query_run_id), rating, comment),
        )
        row = dict(cur.fetchone())
        conn.commit()
        row["id"] = str(row["id"])
        row["query_run_id"] = str(row["query_run_id"])
        if row.get("created_at"):
            row["created_at"] = row["created_at"].isoformat()
        return row


def list_messages(conversation_id: UUID) -> list[dict[str, Any]]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
                SELECT id, conversation_id, role, content, created_at
                FROM app.messages
                WHERE conversation_id = %s
                ORDER BY created_at ASC
                """,
            (str(conversation_id),),
        )
        return [_serialize_message(dict(r)) for r in cur.fetchall()]


def _serialize_message(row: dict[str, Any]) -> dict[str, Any]:
    row["id"] = str(row["id"])
    row["conversation_id"] = str(row["conversation_id"])
    if row.get("created_at"):
        row["created_at"] = row["created_at"].isoformat()
    return row
