from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from insightbridge.config import settings
from insightbridge.demo_sql import try_demo_sql
from insightbridge.memory import format_history_for_prompt
from insightbridge.semantic import load_semantic_layer, semantic_context_for_prompt

SYSTEM_PROMPT = """You are a senior analytics engineer. Given a business question and a semantic layer,
output a single PostgreSQL SELECT query against the analytics schema only.

Respond with JSON only:
{
  "sql": "SELECT ...",
  "assumptions": ["..."],
  "metrics_used": ["mrr"]
}

Never use DML/DDL. Use explicit JOINs. Prefer semantic metric definitions. Include LIMIT <= 1000."""


def generate_sql(
    question: str,
    layer: dict[str, Any] | None = None,
    *,
    history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    layer = layer or load_semantic_layer()
    context = semantic_context_for_prompt(layer)
    hist = format_history_for_prompt(history or [])

    demo = try_demo_sql(question)
    if demo and not settings.openai_api_key:
        return {
            "sql": demo.sql,
            "assumptions": demo.assumptions,
            "metrics_used": [],
            "source": "demo_rules",
        }

    if not settings.openai_api_key:
        raise RuntimeError(
            "No OPENAI_API_KEY set and question did not match demo patterns. "
            "Try: 'What is our MRR?', 'MRR by region', 'Top customers by MRR', 'Churn rate', 'Orders by month'."
        )

    client = OpenAI(api_key=settings.openai_api_key)
    user_content = f"{hist}\n\nSemantic layer:\n{context}\n\nQuestion: {question}"

    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
    )
    raw = response.choices[0].message.content or "{}"
    data = json.loads(raw)
    data["source"] = "llm"
    return data


def synthesize_insight(
    question: str,
    sql: str,
    columns: list[str],
    rows: list[dict[str, Any]],
    assumptions: list[str],
) -> dict[str, Any]:
    preview_rows = rows[:5]
    if settings.openai_api_key:
        client = OpenAI(api_key=settings.openai_api_key)
        payload = {
            "question": question,
            "sql": sql,
            "columns": columns,
            "row_count": len(rows),
            "sample_rows": preview_rows,
            "assumptions": assumptions,
        }
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Write executive-friendly analytics insight as JSON: "
                        '{"headline": "...", "bullets": ["..."], "caveats": ["..."], "follow_ups": ["..."]}. '
                        "Be concise. Note sample size if small."
                    ),
                },
                {"role": "user", "content": json.dumps(payload)},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        return json.loads(response.choices[0].message.content or "{}")

    return _fallback_insight(question, columns, rows, assumptions)


def _fallback_insight(
    question: str,
    columns: list[str],
    rows: list[dict[str, Any]],
    assumptions: list[str],
) -> dict[str, Any]:
    headline = f"Results for: {question[:120]}"
    bullets: list[str] = []
    if len(rows) == 1 and len(columns) == 1:
        bullets.append(f"{columns[0]}: {rows[0].get(columns[0])}")
    elif rows:
        bullets.append(f"Returned {len(rows)} row(s) with columns: {', '.join(columns)}.")
        bullets.append(f"Top row sample: {rows[0]}")
    else:
        bullets.append("Query returned no rows.")
    return {
        "headline": headline,
        "bullets": bullets,
        "caveats": assumptions + ["Demo mode insight (no LLM key)."],
        "follow_ups": [
            "Break this down by region",
            "Show trend by month",
            "Who are the top customers by MRR?",
        ],
    }
