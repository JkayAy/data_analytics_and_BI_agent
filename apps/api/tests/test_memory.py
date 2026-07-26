from insightbridge.memory import expand_follow_up, messages_to_history


def test_expand_follow_up_by_region():
    history = [
        {"role": "user", "text": "What is our total MRR?"},
        {"role": "assistant", "text": "MRR summary", "headline": "MRR summary"},
    ]
    resolved = expand_follow_up("Break that down by region", history)
    assert "region" in resolved.lower()
    assert "mrr" in resolved.lower()


def test_messages_to_history_truncates():
    msgs = []
    for i in range(20):
        msgs.append({"role": "user", "content": {"text": f"q{i}"}})
    hist = messages_to_history(msgs, max_turns=2)
    assert len(hist) <= 4
