from __future__ import annotations

from typing import Any, Protocol


class WarehouseConnector(Protocol):
    """E4: read-only warehouse execution contract."""

    def execute_read_only(
        self,
        sql: str,
        *,
        allowed_schemas: set[str],
        row_limit: int,
        timeout_seconds: int,
    ) -> tuple[list[dict[str, Any]], list[str], int]:
        ...

    def dialect(self) -> str:
        ...
