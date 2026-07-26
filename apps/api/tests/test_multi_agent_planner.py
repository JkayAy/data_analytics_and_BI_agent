from insightbridge.config import settings
from insightbridge.multi_agent import nodes


def test_planner_investigation_mode(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", None)
    state = {"question": "Why is MRR uneven across regions?", "agent_trace": []}
    out = nodes.planner_node(state)
    assert out["mode"] == "investigation"
    assert out["intent"] == "investigation"


def test_planner_standard_metric(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", None)
    state = {"question": "What is our total MRR?", "agent_trace": []}
    out = nodes.planner_node(state)
    assert out["mode"] == "standard"
