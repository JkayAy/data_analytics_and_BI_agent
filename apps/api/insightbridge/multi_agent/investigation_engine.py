from __future__ import annotations

import time
from typing import Any

from insightbridge.config import settings
from insightbridge.demo_sql import try_demo_sql
from insightbridge.semantic import allowed_schemas, pii_columns
from insightbridge.warehouse import WarehouseError, execute_query


def _numeric_and_label_columns(columns: list[str], preview: list[dict[str, Any]]) -> tuple[str | None, str | None]:
    if not preview or not columns:
        return None, None
    sample = preview[0]
    numeric = None
    label = None
    for c in columns:
        v = sample.get(c)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            if numeric is None or c.lower().endswith(("usd", "pct", "count", "mrr")):
                numeric = c
        elif label is None:
            label = c
    if numeric and label == numeric:
        label = next((c for c in columns if c != numeric), None)
    return label, numeric


def rank_drivers(investigation_runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rank top drivers from investigation query results (E3)."""
    ranked: list[dict[str, Any]] = []
    for run in investigation_runs:
        preview = run.get("preview") or []
        columns = run.get("columns") or []
        label_col, num_col = _numeric_and_label_columns(columns, preview)
        if not label_col or not num_col:
            continue
        best_row = max(
            preview,
            key=lambda r: float(r.get(num_col) or 0) if r.get(num_col) is not None else 0,
            default=None,
        )
        if not best_row:
            continue
        ranked.append(
            {
                "driver": str(best_row.get(label_col)),
                "metric": num_col,
                "value": best_row.get(num_col),
                "source": run.get("purpose"),
                "sql": run.get("sql"),
            }
        )
    ranked.sort(key=lambda x: float(x.get("value") or 0), reverse=True)
    for i, item in enumerate(ranked, start=1):
        item["rank"] = i
    return ranked


def run_investigation_queries(state: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    """
    Execute up to N diagnostic queries within time budget.
    Returns (investigation_runs, driver_rankings, total_ms).
    """
    max_queries = settings.investigation_max_queries
    budget_ms = settings.investigation_budget_ms
    started = time.perf_counter()
    total_ms = 0

    layer = load_semantic_layer()
    schemas = allowed_schemas(layer)
    pii = pii_columns(layer)
    runs: list[dict[str, Any]] = []

    question = (state.get("resolved_question") or state.get("question") or "").lower()
    followups: list[tuple[str, str]] = []

    # Demo / deterministic investigation suite
    demos = [
        ("Show MRR by region", "Regional MRR distribution"),
        ("Break down MRR by customer segment", "Segment MRR distribution"),
        ("Show MRR by plan", "Plan tier MRR distribution"),
    ]
    if "order" in question or "revenue" in question and "order" in question:
        demos.append(("Order revenue by month", "Order revenue trend"))

    for phrase, purpose in demos:
        if len(followups) >= max_queries:
            break
        match = try_demo_sql(phrase)
        if match:
            followups.append((purpose, match.sql))

    # LLM-generated follow-ups (fill remaining slots)
    if settings.openai_api_key and state.get("rows") and len(followups) < max_queries:
        import json

        from openai import OpenAI

        from insightbridge.semantic import semantic_context_for_prompt

        client = OpenAI(api_key=settings.openai_api_key)
        ctx = semantic_context_for_prompt(layer)
        remaining = max_queries - len(followups)
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        f'Return JSON {{"followups":[{{"purpose":"...","sql":"SELECT ..."}}]}} '
                        f"Max {remaining} queries, analytics schema, LIMIT 500."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "question": state.get("question"),
                            "primary_sql": state.get("sql"),
                            "sample_rows": (state.get("rows") or [])[:3],
                            "semantic": ctx[:2500],
                        }
                    ),
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        data = json.loads(response.choices[0].message.content or "{}")
        for item in (data.get("followups") or [])[:remaining]:
            if item.get("sql"):
                followups.append((item.get("purpose", "LLM diagnostic"), item["sql"]))

    for purpose, sql in followups:
        elapsed = int((time.perf_counter() - started) * 1000)
        if elapsed >= budget_ms:
            break
        if len(runs) >= max_queries:
            break
        try:
            rows, columns, duration_ms = execute_query(
                sql, allowed_schemas=schemas, pii_columns=pii,
            )
            total_ms += duration_ms
            runs.append(
                {
                    "purpose": purpose,
                    "sql": sql,
                    "columns": columns,
                    "row_count": len(rows),
                    "duration_ms": duration_ms,
                    "preview": rows[:20],
                }
            )
        except WarehouseError:
            continue

    drivers = rank_drivers(runs)
    return runs, drivers, total_ms
