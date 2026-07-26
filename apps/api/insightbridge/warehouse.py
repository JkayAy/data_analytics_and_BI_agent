from __future__ import annotations

import time
from typing import Any

from insightbridge.config import settings
from insightbridge.connectors.postgres import ConnectorExecutionError
from insightbridge.connectors.registry import get_active_connector
from insightbridge.sql_validator import SqlValidationError


class WarehouseError(Exception):
    def __init__(self, message: str, code: str = "warehouse_error"):
        super().__init__(message)
        self.code = code


def execute_query(
    sql: str,
    *,
    allowed_schemas: set[str],
    row_limit: int | None = None,
    pii_columns: set[str] | None = None,
    timeout_seconds: int | None = None,
) -> tuple[list[dict[str, Any]], list[str], int]:
    """Validate and run read-only SQL via active warehouse connector (E4)."""
    limit = row_limit or settings.query_row_limit
    timeout = timeout_seconds or settings.query_timeout_seconds

    connector, _meta = get_active_connector()
    try:
        return connector.execute_read_only(
            sql,
            allowed_schemas=allowed_schemas,
            row_limit=limit,
            timeout_seconds=timeout,
            pii_columns=pii_columns,
        )
    except SqlValidationError:
        raise
    except ConnectorExecutionError as exc:
        raise WarehouseError(str(exc), exc.code) from exc


def explain_query(sql: str, allowed_schemas: set[str]) -> str:
    from insightbridge.sql_validator import ensure_limit, validate_sql

    connector, _ = get_active_connector()
    dialect = connector.dialect()
    validated = validate_sql(sql, allowed_schemas, read_dialect=dialect)
    bounded = ensure_limit(validated, settings.query_row_limit)
    if dialect != "postgres":
        return f"EXPLAIN not supported for {dialect}; SQL validated only."
    import psycopg

    from insightbridge.config import settings as s

    with psycopg.connect(s.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(f"EXPLAIN {bounded}")
            lines = [row[0] for row in cur.fetchall()]
    return "\n".join(lines)


def active_connection_summary() -> dict[str, Any]:
    connector, meta = get_active_connector()
    return {
        "id": meta.get("id"),
        "name": meta.get("name"),
        "dialect": connector.dialect(),
    }
