from __future__ import annotations

import json
from typing import Any
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from insightbridge.config import settings
from insightbridge.crypto import decrypt_json, encrypt_json


def get_conn():
    return psycopg.connect(settings.database_url, row_factory=dict_row)


def _config_from_row(row: dict[str, Any]) -> dict[str, Any]:
    if row.get("config_encrypted"):
        return decrypt_json(row["config_encrypted"])
    cfg = row.get("config_json") or {}
    if isinstance(cfg, str):
        cfg = json.loads(cfg)
    return cfg


def list_connections(org_id: str | None = None) -> list[dict[str, Any]]:
    with get_conn() as conn, conn.cursor() as cur:
        if org_id:
            cur.execute(
                """
                    SELECT id, name, dialect, config_json, is_active, created_at, org_id
                    FROM app.connections WHERE org_id = %s ORDER BY created_at ASC
                    """,
                (org_id,),
            )
        else:
            cur.execute(
                """
                    SELECT id, name, dialect, config_json, is_active, created_at, org_id
                    FROM app.connections ORDER BY created_at ASC
                    """
            )
        out = []
        for row in cur.fetchall():
            item = dict(row)
            item["id"] = str(item["id"])
            cfg = item.get("config_json") or {}
            if isinstance(cfg, str):
                cfg = json.loads(cfg)
            item["config_json"] = _redact_config(item["dialect"], cfg)
            if item.get("org_id"):
                item["org_id"] = str(item["org_id"])
            if item.get("created_at"):
                item["created_at"] = item["created_at"].isoformat()
            out.append(item)
        return out


def get_connection_secrets(connection_id: UUID, org_id: str | None = None) -> dict[str, Any] | None:
    with get_conn() as conn, conn.cursor() as cur:
        if org_id:
            cur.execute(
                """
                    SELECT id, name, dialect, config_json, config_encrypted, org_id
                    FROM app.connections WHERE id = %s AND org_id = %s
                    """,
                (str(connection_id), org_id),
            )
        else:
            cur.execute(
                """
                    SELECT id, name, dialect, config_json, config_encrypted, org_id
                    FROM app.connections WHERE id = %s
                    """,
                (str(connection_id),),
            )
        row = cur.fetchone()
        if not row:
            return None
        item = dict(row)
        item["id"] = str(item["id"])
        item["config_json"] = _config_from_row(item)
        if item["dialect"] == "postgres" and item["config_json"].get("url"):
            from insightbridge.connectors.registry import _normalize_postgres_url

            item["config_json"]["url"] = _normalize_postgres_url(item["config_json"]["url"])
        return item


def get_active_connection_record(org_id: str | None = None) -> dict[str, Any] | None:
    with get_conn() as conn, conn.cursor() as cur:
        if org_id:
            cur.execute(
                """
                    SELECT id, name, dialect, config_json, config_encrypted, is_active, org_id
                    FROM app.connections
                    WHERE is_active = true AND org_id = %s
                    LIMIT 1
                    """,
                (org_id,),
            )
        else:
            cur.execute(
                """
                    SELECT id, name, dialect, config_json, config_encrypted, is_active, org_id
                    FROM app.connections WHERE is_active = true LIMIT 1
                    """
            )
        row = cur.fetchone()
        if not row:
            return None
        item = dict(row)
        item["id"] = str(item["id"])
        item["config_json"] = _config_from_row(item)
        if item["dialect"] == "postgres" and item["config_json"].get("url"):
            from insightbridge.connectors.registry import _normalize_postgres_url

            item["config_json"]["url"] = _normalize_postgres_url(item["config_json"]["url"])
        if item.get("org_id"):
            item["org_id"] = str(item["org_id"])
        return item


def create_connection(
    name: str,
    dialect: str,
    config_json: dict[str, Any],
    *,
    org_id: str,
    set_active: bool = False,
) -> dict[str, Any]:
    encrypted = encrypt_json(config_json)
    redacted = _redact_config(dialect, config_json)
    with get_conn() as conn:
        with conn.cursor() as cur:
            if set_active:
                cur.execute(
                    "UPDATE app.connections SET is_active = false WHERE is_active = true AND org_id = %s",
                    (org_id,),
                )
            cur.execute(
                """
                INSERT INTO app.connections
                  (name, dialect, config_json, config_encrypted, is_active, org_id)
                VALUES (%s, %s, %s::jsonb, %s, %s, %s)
                RETURNING id, name, dialect, is_active, created_at
                """,
                (name, dialect, json.dumps(redacted), encrypted, set_active, org_id),
            )
            row = dict(cur.fetchone())
            conn.commit()
            row["id"] = str(row["id"])
            row["config_json"] = redacted
            if row.get("created_at"):
                row["created_at"] = row["created_at"].isoformat()
            return row


def set_active_connection(connection_id: UUID, org_id: str) -> dict[str, Any] | None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE app.connections SET is_active = false WHERE is_active = true AND org_id = %s",
            (org_id,),
        )
        cur.execute(
            """
                UPDATE app.connections SET is_active = true
                WHERE id = %s AND org_id = %s
                RETURNING id, name, dialect, is_active
                """,
            (str(connection_id), org_id),
        )
        row = cur.fetchone()
        conn.commit()
        if not row:
            return None
        item = dict(row)
        item["id"] = str(item["id"])
        return item


def _redact_config(dialect: str, config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(config, dict):
        return {}
    copy = dict(config)
    for key in ("password", "private_key", "credentials_path"):
        if copy.get(key):
            copy[key] = "***"
    if dialect == "postgres" and copy.get("url"):
        copy["url"] = _redact_url(copy["url"])
    return copy


def _redact_url(url: str) -> str:
    if "@" in url:
        prefix, rest = url.split("@", 1)
        if "://" in prefix:
            scheme, _creds = prefix.split("://", 1)
            return f"{scheme}://***@{rest}"
    return url
