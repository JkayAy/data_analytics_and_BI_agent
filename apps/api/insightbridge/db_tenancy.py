from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

import psycopg
from psycopg.rows import dict_row

from insightbridge.config import settings


def get_conn():
    return psycopg.connect(settings.database_url, row_factory=dict_row)


def upsert_user_by_email(email: str, name: str | None = None) -> dict[str, Any]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app.users (email, name)
                VALUES (%s, %s)
                ON CONFLICT (email) DO UPDATE SET name = COALESCE(EXCLUDED.name, app.users.name)
                RETURNING id, email, name, created_at
                """,
                (email.lower(), name),
            )
            row = dict(cur.fetchone())
            conn.commit()
            row["id"] = str(row["id"])
            row["default_org_id"] = settings.default_org_id
            return row


def get_member(user_id: str, org_id: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT org_id, user_id, role, created_at
                FROM app.organization_members
                WHERE user_id = %s AND org_id = %s
                """,
                (user_id, org_id),
            )
            row = cur.fetchone()
            if not row:
                return None
            item = dict(row)
            item["org_id"] = str(item["org_id"])
            item["user_id"] = str(item["user_id"])
            return item


def issue_magic_link(email: str, token_hash: str, expire_minutes: int) -> None:
    expires = datetime.now(UTC) + timedelta(minutes=expire_minutes)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app.magic_link_tokens (email, token_hash, expires_at)
                VALUES (%s, %s, %s)
                """,
                (email, token_hash, expires),
            )
            conn.commit()


def consume_magic_link(token_hash: str) -> str | None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, email FROM app.magic_link_tokens
                WHERE token_hash = %s AND used_at IS NULL AND expires_at > NOW()
                """,
                (token_hash,),
            )
            row = cur.fetchone()
            if not row:
                return None
            cur.execute(
                "UPDATE app.magic_link_tokens SET used_at = NOW() WHERE id = %s",
                (row["id"],),
            )
            conn.commit()
            return row["email"]


def log_audit(
    org_id: str | None,
    actor_user_id: str | None,
    action: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    metadata: dict | None = None,
) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app.audit_events
                  (org_id, actor_user_id, action, resource_type, resource_id, metadata_json)
                VALUES (%s, %s, %s, %s, %s, %s::jsonb)
                """,
                (
                    org_id,
                    actor_user_id,
                    action,
                    resource_type,
                    resource_id,
                    json.dumps(metadata) if metadata else None,
                ),
            )
            conn.commit()


def get_me(user_id: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT u.id, u.email, u.name,
                       m.org_id, m.role, o.name AS org_name, o.slug AS org_slug
                FROM app.users u
                JOIN app.organization_members m ON m.user_id = u.id
                JOIN app.organizations o ON o.id = m.org_id
                WHERE u.id = %s
                LIMIT 1
                """,
                (user_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            item = dict(row)
            item["id"] = str(item["id"])
            item["org_id"] = str(item["org_id"])
            return item


def ensure_org_member(org_id: str, user_id: str, role: str = "member") -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app.organization_members (org_id, user_id, role)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                (org_id, user_id, role),
            )
            conn.commit()
