from __future__ import annotations

import time
from typing import Any

from insightbridge.sql_validator import ensure_limit, mask_pii_columns, validate_sql


class ConnectorExecutionError(Exception):
    def __init__(self, message: str, code: str = "connector_error"):
        super().__init__(message)
        self.code = code


class SnowflakeConnector:
    """Read-only Snowflake. Requires snowflake-connector-python."""

    def __init__(self, config: dict[str, Any]):
        required = ("account", "user", "password", "warehouse", "database")
        missing = [k for k in required if not config.get(k)]
        if missing:
            raise ValueError(f"Snowflake config missing: {', '.join(missing)}")
        self.config = config

    def dialect(self) -> str:
        return "snowflake"

    def _connect(self):
        try:
            import snowflake.connector
        except ImportError as exc:
            raise ConnectorExecutionError(
                "Install snowflake-connector-python to use Snowflake connector",
                "missing_dependency",
            ) from exc
        cfg = self.config
        return snowflake.connector.connect(
            account=cfg["account"],
            user=cfg["user"],
            password=cfg["password"],
            warehouse=cfg["warehouse"],
            database=cfg["database"],
            schema=cfg.get("schema", "ANALYTICS"),
            role=cfg.get("role"),
        )

    def test(self) -> str:
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.fetchone()
        finally:
            conn.close()
        return f"Snowflake OK (account={self.config['account']})"

    def execute_read_only(
        self,
        sql: str,
        *,
        allowed_schemas: set[str],
        row_limit: int,
        timeout_seconds: int,
        pii_columns: set[str] | None = None,
    ) -> tuple[list[dict[str, Any]], list[str], int]:
        validated = validate_sql(sql, allowed_schemas, read_dialect="snowflake")
        bounded = ensure_limit(validated, row_limit)
        start = time.perf_counter()
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(f"ALTER SESSION SET STATEMENT_TIMEOUT_IN_SECONDS = {timeout_seconds}")
            cur.execute(bounded)
            columns = [desc[0] for desc in cur.description] if cur.description else []
            raw = cur.fetchmany(row_limit)
            rows = [dict(zip(columns, r)) for r in raw]
        except Exception as exc:
            raise ConnectorExecutionError(str(exc), "sf_error") from exc
        finally:
            conn.close()

        duration_ms = int((time.perf_counter() - start) * 1000)
        serializable = [{k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in row.items()} for row in rows]
        return mask_pii_columns(serializable, pii_columns or set()), columns, duration_ms
