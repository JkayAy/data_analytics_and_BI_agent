"""End-to-end demo mode: ask → SQL → governance → execute → insight + trace."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from insightbridge.agent import run_agent

EXPECTED_AGENTS = [
    "Planner",
    "SQL Specialist",
    "Governance",
    "Executor",
    "Investigation",
    "Analyst",
    "Visualization",
    "QA Critic",
]

README_QUESTIONS = [
    ("What is our total MRR?", {"min_rows": 1, "sql_contains": "mrr_usd"}),
    ("Show MRR by region", {"min_rows": 2, "sql_contains": "GROUP BY c.region"}),
    ("What is our churn rate?", {"min_rows": 1, "sql_contains": "churn_pct"}),
    ("Top 10 customers by MRR", {"min_rows": 2, "sql_contains": "LIMIT 10"}),
    ("Order revenue by month", {"min_rows": 1, "sql_contains": "DATE_TRUNC"}),
    (
        "Why is MRR uneven across regions?",
        {"min_rows": 2, "sql_contains": "GROUP BY c.region", "mode": "investigation"},
    ),
]


@pytest.fixture(autouse=True)
def demo_mode(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("insightbridge.config.settings.openai_api_key", None)


@pytest.mark.parametrize("question,expect", README_QUESTIONS)
def test_demo_run_agent(question: str, expect: dict):
    result = run_agent(question)
    assert result.status == "success", result.error
    assert result.sql
    assert "SELECT" in result.sql.upper()
    assert expect["sql_contains"].lower() in result.sql.lower()
    assert result.row_count >= expect["min_rows"]
    assert result.insight.get("headline")
    assert result.chart_spec is not None
    assert [s["agent"] for s in result.agent_trace] == EXPECTED_AGENTS
    if expect.get("mode") == "investigation":
        assert result.mode == "investigation"
        assert len(result.investigation_runs) >= 1
        assert len(result.driver_rankings) >= 1


def test_demo_api_ask_creates_audit_row():
    from insightbridge.main import app

    client = TestClient(app)
    health = client.get("/health").json()
    assert health["status"] == "ok"
    assert health["demo_mode"] is True

    conv = client.post("/v1/conversations", json={"title": "test"}).json()
    resp = client.post(
        f"/v1/conversations/{conv['id']}/ask",
        json={"question": "What is our total MRR?"},
    )
    assert resp.status_code == 200
    body = resp.json()
    content = body["assistant_message"]["content"]
    assert content["status"] == "success"
    assert content["query_run_id"]
    assert body["query_run_id"]

    audit = client.get("/v1/audit/query-runs?limit=5").json()
    ids = [r["id"] for r in audit["items"]]
    assert body["query_run_id"] in ids
