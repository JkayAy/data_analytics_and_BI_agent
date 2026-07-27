from __future__ import annotations

import re
from typing import Any

import sqlglot
from sqlglot import exp

FORBIDDEN = frozenset(
    {"insert", "update", "delete", "drop", "truncate", "alter", "create", "grant", "revoke"}
)


class SqlValidationError(Exception):
    def __init__(self, message: str, code: str = "validation_error"):
        super().__init__(message)
        self.code = code


def validate_sql(
    sql: str,
    allowed_schemas: set[str] | None = None,
    *,
    read_dialect: str = "postgres",
) -> str:
    """Parse, normalize, and enforce read-only SELECT policies."""
    dialect = read_dialect.lower()
    stripped = sql.strip().rstrip(";")
    if not stripped:
        raise SqlValidationError("Empty SQL", "empty_sql")

    if ";" in stripped:
        raise SqlValidationError("Multiple statements are not allowed", "multi_statement")

    try:
        parsed = sqlglot.parse_one(stripped, read=dialect)
    except Exception as exc:
        raise SqlValidationError(f"Invalid SQL: {exc}", "parse_error") from exc

    if not isinstance(parsed, exp.Select):
        raise SqlValidationError("Only SELECT queries are allowed", "not_select")

    for node in parsed.walk():
        kind = node.key.lower() if hasattr(node, "key") else ""
        if kind in FORBIDDEN or type(node).__name__.lower() in FORBIDDEN:
            raise SqlValidationError(f"Forbidden operation: {type(node).__name__}", "forbidden_op")

    normalized = parsed.sql(dialect=dialect)

    if allowed_schemas:
        allowed = {s.lower() for s in allowed_schemas}
        for table in parsed.find_all(exp.Table):
            if not table.db and dialect in ("bigquery", "snowflake"):
                continue
            schema = (table.db or "public").lower()
            if schema not in allowed:
                hint = ", ".join(sorted(allowed_schemas))
                name = f"{table.db}.{table.name}" if table.db else str(table.name)
                raise SqlValidationError(
                    f"Table `{name}` must use an allowed schema/dataset ({hint}).",
                    "schema_denied",
                )

    return normalized


def ensure_limit(sql: str, max_rows: int) -> str:
    """Append LIMIT if missing (case-insensitive check on normalized SQL)."""
    if re.search(r"\blimit\s+\d+", sql, re.IGNORECASE):
        return sql
    return f"{sql.rstrip()} LIMIT {max_rows}"


def mask_pii_columns(rows: list[dict[str, Any]], pii_columns: set[str]) -> list[dict[str, Any]]:
    if not pii_columns:
        return rows
    masked = []
    for row in rows:
        copy = dict(row)
        for col in pii_columns:
            if col in copy and copy[col] is not None:
                copy[col] = "***"
        masked.append(copy)
    return masked
