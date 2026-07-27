from __future__ import annotations

import json
import re
import time

from insightbridge.config import settings
from insightbridge.llm import generate_sql
from insightbridge.memory import format_history_for_prompt, planner_context_from_history
from insightbridge.multi_agent.state import AgentTraceStep, BIAgentState
from insightbridge.semantic import load_semantic_layer

INVESTIGATION_PATTERN = re.compile(
    r"\b(why|root cause|drivers?|decline|dropped|explain|investigate)\b",
    re.IGNORECASE,
)


def _trace(state: BIAgentState, agent: str, action: str, detail: str, start: float) -> None:
    ms = int((time.perf_counter() - start) * 1000)
    steps = list(state.get("agent_trace") or [])
    steps.append(
        AgentTraceStep(agent=agent, action=action, detail=detail[:2000], duration_ms=ms),
    )
    state["agent_trace"] = steps


def planner_node(state: BIAgentState) -> BIAgentState:
    start = time.perf_counter()
    question = state.get("resolved_question") or state["question"]
    history = state.get("history") or []
    investigation = bool(INVESTIGATION_PATTERN.search(question))

    hist_block = format_history_for_prompt(history)
    hist_hint = planner_context_from_history(history)

    if settings.openai_api_key:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        prompt = f"{hist_block}\n{hist_hint}\n\nCurrent question: {state['question']}\nResolved: {question}"
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Return JSON: "
                        '{"intent":"metric|breakdown|trend|investigation","mode":"standard|investigation",'
                        '"plan_steps":["..."],"reasoning":"..."}. '
                        "Use investigation mode when user asks why or root cause."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        data = json.loads(response.choices[0].message.content or "{}")
        state["intent"] = data.get("intent", "metric")
        state["mode"] = data.get("mode", "standard")
        state["plan_steps"] = data.get("plan_steps") or []
        state["planner_reasoning"] = data.get("reasoning", "")
    else:
        state["intent"] = "investigation" if investigation else "metric"
        if re.search(r"\b(region|segment|plan|month|trend)\b", question, re.IGNORECASE):
            state["intent"] = "breakdown"
        state["mode"] = "investigation" if investigation else "standard"
        state["plan_steps"] = (
            ["Run primary metric query", "Run dimensional breakdown for drivers"]
            if investigation
            else ["Generate SQL from semantic layer", "Validate and execute", "Summarize for executives"]
        )
        state["planner_reasoning"] = "Rule-based planner (demo mode)"

    _trace(
        state,
        "Planner",
        "plan",
        f"intent={state['intent']} mode={state['mode']} steps={len(state['plan_steps'])}",
        start,
    )
    return state


def sql_specialist_node(state: BIAgentState) -> BIAgentState:
    start = time.perf_counter()

    attempts = state.get("sql_attempts", 0) + 1
    state["sql_attempts"] = attempts
    layer = load_semantic_layer()
    question = state.get("resolved_question") or state["question"]
    if state.get("validation_error") and attempts > 1:
        question = f"{question}\n\nFix SQL error: {state['validation_error']}"

    payload = generate_sql(question, layer, history=state.get("history"))
    state["sql"] = payload["sql"]
    state["assumptions"] = payload.get("assumptions") or []
    state["metrics_used"] = payload.get("metrics_used") or []
    state["sql_source"] = payload.get("source", "unknown")
    state["validation_error"] = None
    _trace(state, "SQL Specialist", "generate_sql", state["sql"][:500], start)
    return state


def governance_node(state: BIAgentState) -> BIAgentState:
    start = time.perf_counter()
    from insightbridge.semantic import allowed_schemas
    from insightbridge.sql_validator import SqlValidationError, validate_sql

    layer = load_semantic_layer()
    try:
        from insightbridge.connectors.registry import get_active_connector

        dialect = get_active_connector()[0].dialect()
        validate_sql(state.get("sql", ""), allowed_schemas(layer), read_dialect=dialect)
        state["validation_error"] = None
        _trace(state, "Governance", "validate", "SQL passed policy checks", start)
    except SqlValidationError as exc:
        state["validation_error"] = str(exc)
        state["error_code"] = exc.code
        _trace(state, "Governance", "reject", str(exc), start)
    return state


def executor_node(state: BIAgentState) -> BIAgentState:
    start = time.perf_counter()
    from insightbridge.semantic import allowed_schemas, pii_columns
    from insightbridge.warehouse import WarehouseError, execute_query

    layer = load_semantic_layer()
    try:
        rows, columns, duration_ms = execute_query(
            state["sql"],
            allowed_schemas=allowed_schemas(layer),
            pii_columns=pii_columns(layer),
        )
        state["rows"] = rows
        state["columns"] = columns
        state["duration_ms"] = duration_ms
        state["result_preview"] = rows[:50]
        state["status"] = "success"
        state["error"] = None
        _trace(state, "Executor", "execute", f"{len(rows)} rows in {duration_ms}ms", start)
    except WarehouseError as exc:
        state["validation_error"] = str(exc)
        state["error"] = str(exc)
        state["error_code"] = exc.code
        state["rows"] = []
        state["columns"] = []
        _trace(state, "Executor", "error", str(exc), start)
    return state


def investigation_node(state: BIAgentState) -> BIAgentState:
    start = time.perf_counter()
    if state.get("mode") != "investigation":
        _trace(state, "Investigation", "skip", "standard mode", start)
        return state

    from insightbridge.multi_agent.investigation_engine import run_investigation_queries

    runs, drivers, inv_ms = run_investigation_queries(state)
    state["investigation_runs"] = runs
    state["driver_rankings"] = drivers
    _trace(
        state,
        "Investigation",
        "diagnose",
        f"{len(runs)} queries, {len(drivers)} ranked drivers, {inv_ms}ms",
        start,
    )
    return state


def analyst_node(state: BIAgentState) -> BIAgentState:
    start = time.perf_counter()
    from insightbridge.llm import synthesize_insight

    if state.get("error") and not state.get("rows"):
        state["insight"] = {
            "headline": "Could not complete analysis",
            "bullets": [state.get("error") or "Unknown error"],
            "caveats": [],
            "follow_ups": [],
        }
        _trace(state, "Analyst", "fail", state.get("error") or "", start)
        return state

    base = synthesize_insight(
        state.get("resolved_question") or state["question"],
        state.get("sql", ""),
        state.get("columns") or [],
        state.get("rows") or [],
        state.get("assumptions") or [],
    )
    inv = state.get("investigation_runs") or []
    drivers = state.get("driver_rankings") or []
    if inv:
        bullets = list(base.get("bullets") or [])
        bullets.append("Investigation follow-ups:")
        for run in inv:
            bullets.append(f"- {run['purpose']}: {run['row_count']} rows")
        base["bullets"] = bullets
    if drivers:
        bullets = list(base.get("bullets") or [])
        bullets.append("Top ranked drivers:")
        for d in drivers[:5]:
            bullets.append(f"- #{d.get('rank')} {d.get('driver')} ({d.get('metric')}: {d.get('value')})")
        base["bullets"] = bullets
        base["driver_rankings"] = drivers
    if inv:
        caveats = list(base.get("caveats") or [])
        caveats.append("Investigation mode: see agent trace and ranked drivers.")
        base["caveats"] = caveats
    state["insight"] = base
    _trace(state, "Analyst", "synthesize", base.get("headline", "")[:200], start)
    return state


def visualization_node(state: BIAgentState) -> BIAgentState:
    start = time.perf_counter()
    from insightbridge.charts import infer_chart_spec

    state["chart_spec"] = infer_chart_spec(
        state.get("columns") or [],
        state.get("rows") or [],
    )
    _trace(
        state,
        "Visualization",
        "chart_spec",
        (state["chart_spec"] or {}).get("type", "none"),
        start,
    )
    return state


def qa_critic_node(state: BIAgentState) -> BIAgentState:
    start = time.perf_counter()
    retries = state.get("qa_retries", 0)

    if state.get("validation_error") or state.get("error"):
        state["qa_passed"] = False
        state["qa_notes"] = state.get("validation_error") or state.get("error") or "failed"
        _trace(state, "QA Critic", "reject", state["qa_notes"], start)
        return state

    rows = state.get("rows") or []
    if settings.openai_api_key:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": 'Return JSON {"passed": true/false, "notes": "..."}',
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "question": state["question"],
                            "sql": state.get("sql"),
                            "row_count": len(rows),
                            "headline": (state.get("insight") or {}).get("headline"),
                        }
                    ),
                },
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        data = json.loads(response.choices[0].message.content or "{}")
        state["qa_passed"] = bool(data.get("passed", True))
        state["qa_notes"] = data.get("notes", "")
    else:
        state["qa_passed"] = len(rows) > 0 or "churn" in state["question"].lower()
        state["qa_notes"] = "Heuristic QA (demo mode)"

    if not state.get("qa_passed"):
        state["qa_retries"] = retries + 1
    else:
        state["qa_retries"] = retries

    _trace(state, "QA Critic", "review", f"passed={state['qa_passed']}", start)
    return state
