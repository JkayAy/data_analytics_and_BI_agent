from datetime import datetime
from zoneinfo import ZoneInfo

from insightbridge.agent import AgentResult
from insightbridge.delivery.formatters import format_slack_payload, format_teams_payload


def _sample_result() -> AgentResult:
    return AgentResult(
        sql="SELECT 1",
        assumptions=[],
        metrics_used=["mrr"],
        sql_source="demo",
        status="success",
        row_count=1,
        duration_ms=42,
        columns=["mrr"],
        rows=[{"mrr": 100}],
        result_preview=[{"mrr": 100}],
        chart_spec=None,
        insight={"headline": "MRR is $100", "bullets": ["Stable growth"], "caveats": [], "follow_ups": []},
        agent_trace=[],
        investigation_runs=[],
        driver_rankings=[],
        intent="metric",
        mode="standard",
        plan_steps=[],
        resolved_question=None,
    )


def test_slack_blocks():
    payload = format_slack_payload(_sample_result(), title="Weekly", question="Total MRR?")
    assert payload["text"] == "MRR is $100"
    assert any(b.get("type") == "header" for b in payload["blocks"])


def test_teams_card():
    payload = format_teams_payload(_sample_result(), title="Weekly", question="Total MRR?")
    assert payload["title"] == "Weekly"
    assert payload["sections"][0]["facts"][0]["title"] == "Question"
