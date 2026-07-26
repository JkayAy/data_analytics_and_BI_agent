from __future__ import annotations

from insightbridge.config import settings
from insightbridge.multi_agent import nodes
from insightbridge.multi_agent.state import BIAgentState

GRAPH_VERSION = "1.1.0"

PHASE_STATUS = {
    "E0_foundation": "done",
    "E1_multi_agent_core": "done",
    "E2_conversation_memory": "done",
    "E3_investigation_mode": "done",
    "E4_connectors": "done",
    "E5_tenancy": "done",
    "E6_delivery": "done",
}

AGENT_CAPABILITIES = [
    {"id": "planner", "name": "Planner Agent", "role": "Intent classification and execution plan"},
    {"id": "sql_specialist", "name": "SQL Specialist", "role": "Semantic-layer-aware SQL generation"},
    {"id": "governance", "name": "Governance Agent", "role": "sqlglot policy enforcement (deterministic)"},
    {"id": "executor", "name": "Executor Agent", "role": "Warehouse execution and profiling"},
    {"id": "investigation", "name": "Investigation Agent", "role": "Multi-query driver analysis"},
    {"id": "analyst", "name": "Analyst Agent", "role": "Executive narrative synthesis"},
    {"id": "visualization", "name": "Visualization Agent", "role": "Chart specification"},
    {"id": "qa_critic", "name": "QA Critic Agent", "role": "Answer quality gate"},
]


def _route_after_governance(state: BIAgentState) -> str:
    if state.get("validation_error"):
        if state.get("sql_attempts", 0) < 3:
            return "sql_specialist"
        return "failed"
    if state.get("error") and not state.get("rows"):
        if state.get("sql_attempts", 0) < 3:
            return "sql_specialist"
        return "failed"
    return "executor"


def _route_after_executor(state: BIAgentState) -> str:
    if state.get("validation_error") and not state.get("rows"):
        if state.get("sql_attempts", 0) < 3:
            return "sql_specialist"
        return "failed"
    return "investigation"


def _route_after_qa(state: BIAgentState) -> str:
    if state.get("qa_passed"):
        return "done"
    if state.get("qa_retries", 0) <= 1:
        return "sql_specialist"
    return "done"


def _failed_node(state: BIAgentState) -> BIAgentState:
    state["status"] = "failed"
    if not state.get("insight"):
        state["insight"] = {
            "headline": "Analysis failed",
            "bullets": [state.get("error") or state.get("validation_error") or "Policy or warehouse error"],
            "caveats": [],
            "follow_ups": [],
        }
    return state


def _finalize_node(state: BIAgentState) -> BIAgentState:
    if state.get("status") != "failed":
        state["status"] = "success" if state.get("qa_passed", True) else "success_with_warnings"
        if not state.get("qa_passed"):
            insight = dict(state.get("insight") or {})
            caveats = list(insight.get("caveats") or [])
            caveats.append(f"QA notes: {state.get('qa_notes', '')}")
            insight["caveats"] = caveats
            state["insight"] = insight
    return state


def run_multi_agent(question: str, history: list | None = None) -> BIAgentState:
    """Run the multi-agent pipeline (LangGraph when enabled, else sequential)."""
    from insightbridge.memory import expand_follow_up

    resolved = expand_follow_up(question, history or [])
    initial: BIAgentState = {
        "question": question,
        "resolved_question": resolved,
        "history": history or [],
        "agent_trace": [],
        "sql_attempts": 0,
        "qa_retries": 0,
        "investigation_runs": [],
        "driver_rankings": [],
        "status": "running",
    }

    if settings.multi_agent_use_langgraph:
        return _run_langgraph(initial)
    return _run_sequential(initial)


def _run_sequential(state: BIAgentState) -> BIAgentState:
    """Deterministic orchestration — same agents, no LangGraph dependency."""
    max_outer = 5
    for _ in range(max_outer):
        state = nodes.planner_node(state)
        while True:
            state = nodes.sql_specialist_node(state)
            state = nodes.governance_node(state)
            route = _route_after_governance(state)
            if route == "sql_specialist":
                continue
            if route == "failed":
                return _finalize_node(_failed_node(state))
            break

        state = nodes.executor_node(state)
        route = _route_after_executor(state)
        if route == "sql_specialist":
            continue
        if route == "failed":
            return _finalize_node(_failed_node(state))

        state = nodes.investigation_node(state)
        state = nodes.analyst_node(state)
        state = nodes.visualization_node(state)
        state = nodes.qa_critic_node(state)

        qa_route = _route_after_qa(state)
        if qa_route == "sql_specialist":
            continue
        return _finalize_node(state)

    return _finalize_node(_failed_node(state))


def _run_langgraph(state: BIAgentState) -> BIAgentState:
    try:
        from langgraph.graph import END, StateGraph
    except ImportError:
        return _run_sequential(state)

    graph = StateGraph(BIAgentState)

    graph.add_node("planner", nodes.planner_node)
    graph.add_node("sql_specialist", nodes.sql_specialist_node)
    graph.add_node("governance", nodes.governance_node)
    graph.add_node("executor", nodes.executor_node)
    graph.add_node("investigation", nodes.investigation_node)
    graph.add_node("analyst", nodes.analyst_node)
    graph.add_node("visualization", nodes.visualization_node)
    graph.add_node("qa_critic", nodes.qa_critic_node)
    graph.add_node("finalize", _finalize_node)
    graph.add_node("failed", _failed_node)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "sql_specialist")
    graph.add_edge("sql_specialist", "governance")

    graph.add_conditional_edges(
        "governance",
        _route_after_governance,
        {"sql_specialist": "sql_specialist", "executor": "executor", "failed": "failed"},
    )

    graph.add_conditional_edges(
        "executor",
        _route_after_executor,
        {"sql_specialist": "sql_specialist", "investigation": "investigation", "failed": "failed"},
    )

    graph.add_edge("investigation", "analyst")
    graph.add_edge("analyst", "visualization")
    graph.add_edge("visualization", "qa_critic")

    graph.add_conditional_edges(
        "qa_critic",
        _route_after_qa,
        {"sql_specialist": "sql_specialist", "done": "finalize"},
    )

    graph.add_edge("finalize", END)
    graph.add_edge("failed", END)

    app = graph.compile()
    return app.invoke(state)
