from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from insightbridge.multi_agent.graph import run_multi_agent


@dataclass
class AgentResult:
    sql: str
    assumptions: list[str]
    metrics_used: list[str]
    sql_source: str
    status: str
    row_count: int
    duration_ms: int
    columns: list[str]
    rows: list[dict[str, Any]]
    result_preview: list[dict[str, Any]]
    chart_spec: dict[str, Any] | None
    insight: dict[str, Any]
    agent_trace: list[dict[str, Any]]
    investigation_runs: list[dict[str, Any]]
    driver_rankings: list[dict[str, Any]]
    intent: str | None
    mode: str | None
    plan_steps: list[str]
    resolved_question: str | None
    error: str | None = None
    error_code: str | None = None


def run_agent(question: str, *, history: list[dict[str, Any]] | None = None, max_retries: int = 2) -> AgentResult:
    """Enterprise multi-agent entry point (max_retries kept for API compatibility)."""
    del max_retries
    final = run_multi_agent(question, history=history)
    rows = final.get("rows") or []
    return AgentResult(
        sql=final.get("sql") or "",
        assumptions=final.get("assumptions") or [],
        metrics_used=final.get("metrics_used") or [],
        sql_source=final.get("sql_source", "unknown"),
        status=final.get("status", "failed"),
        row_count=len(rows),
        duration_ms=final.get("duration_ms") or 0,
        columns=final.get("columns") or [],
        rows=rows,
        result_preview=final.get("result_preview") or rows[:50],
        chart_spec=final.get("chart_spec"),
        insight=final.get("insight")
        or {
            "headline": "No insight",
            "bullets": [],
            "caveats": [],
            "follow_ups": [],
        },
        agent_trace=list(final.get("agent_trace") or []),
        investigation_runs=list(final.get("investigation_runs") or []),
        driver_rankings=list(final.get("driver_rankings") or []),
        intent=final.get("intent"),
        mode=final.get("mode"),
        plan_steps=list(final.get("plan_steps") or []),
        resolved_question=final.get("resolved_question"),
        error=final.get("error"),
        error_code=final.get("error_code"),
    )
