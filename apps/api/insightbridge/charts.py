from __future__ import annotations

import re
from typing import Any


def infer_chart_spec(columns: list[str], rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not rows or not columns:
        return None

    # Single scalar
    if len(rows) == 1 and len(columns) == 1:
        col = columns[0]
        val = rows[0].get(col)
        return {
            "type": "metric",
            "label": col.replace("_", " ").title(),
            "value": val,
        }

    time_col = _find_time_column(columns)
    numeric_cols = _numeric_columns(columns, rows)

    if time_col and numeric_cols:
        return {
            "type": "line",
            "x": time_col,
            "y": numeric_cols[0],
            "data": rows[:500],
        }

    cat_col = _find_category_column(columns, numeric_cols)
    if cat_col and numeric_cols:
        return {
            "type": "bar",
            "x": cat_col,
            "y": numeric_cols[0],
            "data": rows[:50],
        }

    if len(columns) >= 2:
        return {
            "type": "table",
            "columns": columns,
            "data": rows[:100],
        }
    return None


def _find_time_column(columns: list[str]) -> str | None:
    for c in columns:
        cl = c.lower()
        if any(k in cl for k in ("date", "month", "week", "day", "period", "created_at")):
            return c
    return None


def _find_category_column(columns: list[str], numeric_cols: list[str]) -> str | None:
    numeric_set = set(numeric_cols)
    for c in columns:
        if c not in numeric_set:
            cl = c.lower()
            if any(k in cl for k in ("region", "segment", "plan", "name", "category", "product")):
                return c
    for c in columns:
        if c not in numeric_set:
            return c
    return None


def _numeric_columns(columns: list[str], rows: list[dict[str, Any]]) -> list[str]:
    nums: list[str] = []
    sample = rows[0]
    for c in columns:
        v = sample.get(c)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            nums.append(c)
        elif v is not None and _looks_numeric(v):
            nums.append(c)
    return nums


def _looks_numeric(v: Any) -> bool:
    if isinstance(v, str):
        try:
            float(v.replace(",", ""))
            return True
        except ValueError:
            return False
    return False
