from __future__ import annotations

import json
import time
from typing import Any

import psycopg
from psycopg.rows import dict_row

from insightbridge.sql_validator import ensure_limit, mask_pii_columns, validate_sql


class ConnectorExecutionError(Exception):
    def __init__(self, message: str, code: str = "connector_error"):
        super().__init__(message)
        self.code = code


class PostgresConnector:
    def __init__(self, config: dict[str, Any]):
        self.url = config.get("url") or config.get("database_url")
        if not self.url:
            raise ValueError("Postgres config requires 'url'")

    def dialect(self) -> str:
        return "postgres"

    def test(self) -> str:
        with psycopg.connect(self.url) as conn, conn.cursor() as cur:
            cur.execute("SELECT 1 AS ok")
            row = cur.fetchone()
        return f"Postgres OK ({row[0] if row else 1})"

    def execute_read_only(
        self,
        sql: str,
        *,
        allowed_schemas: set[str],
        row_limit: int,
        timeout_seconds: int,
        pii_columns: set[str] | None = None,
    ) -> tuple[list[dict[str, Any]], list[str], int]:
        validated = validate_sql(sql, allowed_schemas, read_dialect="postgres")
        bounded = ensure_limit(validated, row_limit)
        start = time.perf_counter()
        try:
            with psycopg.connect(self.url, row_factory=dict_row) as conn:
                conn.execute(f"SET statement_timeout = '{timeout_seconds * 1000}'")
                with conn.cursor() as cur:
                    cur.execute(bounded)
                    rows = cur.fetchall()
                    columns = [desc.name for desc in cur.description] if cur.description else []
        except psycopg.Error as exc:
            raise ConnectorExecutionError(str(exc), "db_error") from exc

        duration_ms = int((time.perf_counter() - start) * 1000)
        serializable = [_json_safe_row(dict(r)) for r in rows]
        return mask_pii_columns(serializable, pii_columns or set()), columns, duration_ms


def _json_safe_row(row: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in row.items():
        if hasattr(v, "isoformat"):
            out[k] = v.isoformat()
        elif isinstance(v, (dict, list)):
            out[k] = json.dumps(v) if isinstance(v, dict) else v
        else:
            out[k] = v
    return out
