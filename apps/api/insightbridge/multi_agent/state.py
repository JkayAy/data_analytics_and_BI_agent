from __future__ import annotations

from typing import Any, TypedDict


class AgentTraceStep(TypedDict):
    agent: str
    action: str
    detail: str
    duration_ms: int


class InvestigationRun(TypedDict):
    purpose: str
    sql: str
    columns: list[str]
    row_count: int
    duration_ms: int
    preview: list[dict[str, Any]]


class BIAgentState(TypedDict, total=False):
    question: str
    history: list[dict[str, Any]]
    intent: str
    mode: str
    plan_steps: list[str]
    planner_reasoning: str
    sql: str
    sql_attempts: int
    assumptions: list[str]
    metrics_used: list[str]
    sql_source: str
    validation_error: str | None
    columns: list[str]
    rows: list[dict[str, Any]]
    result_preview: list[dict[str, Any]]
    duration_ms: int
    investigation_runs: list[InvestigationRun]
    driver_rankings: list[dict[str, Any]]
    resolved_question: str
    chart_spec: dict[str, Any] | None
    insight: dict[str, Any]
    qa_passed: bool
    qa_notes: str
    qa_retries: int
    agent_trace: list[AgentTraceStep]
    status: str
    error: str | None
    error_code: str | None
