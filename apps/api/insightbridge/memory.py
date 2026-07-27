from __future__ import annotations

import re
from typing import Any

FOLLOW_UP_PATTERN = re.compile(
    r"\b(break (it )?down|by region|by segment|same for|that|those|what about|"
    r"drill down|more detail|expand|split by|per region|per segment)\b",
    re.IGNORECASE,
)


def messages_to_history(messages: list[dict[str, Any]], *, max_turns: int = 6) -> list[dict[str, Any]]:
    """Convert stored messages to compact history for agents."""
    history: list[dict[str, Any]] = []
    for msg in messages[-max_turns * 2 :]:
        role = msg.get("role")
        content = msg.get("content") or {}
        if isinstance(content, str):
            text = content
            extra: dict[str, Any] = {}
        else:
            text = content.get("text") or content.get("headline") or ""
            if role == "assistant" and not text:
                insight = content.get("insight") or {}
                text = insight.get("headline") or ""
            extra = {
                "sql": content.get("sql"),
                "headline": (content.get("insight") or {}).get("headline"),
                "mode": content.get("mode"),
            }
        if text:
            entry: dict[str, Any] = {"role": role, "text": text}
            entry.update({k: v for k, v in extra.items() if v})
            history.append(entry)
    return history


def format_history_for_prompt(history: list[dict[str, Any]]) -> str:
    if not history:
        return ""
    lines = ["Conversation history (most recent last):"]
    for turn in history[-8:]:
        role = turn.get("role", "user")
        text = turn.get("text", "")
        lines.append(f"- {role}: {text}")
        if turn.get("sql") and role == "assistant":
            lines.append(f"  (prior SQL snippet: {str(turn['sql'])[:200]}...)")
    return "\n".join(lines)


def expand_follow_up(question: str, history: list[dict[str, Any]]) -> str:
    """
    Resolve short follow-ups using prior user question + assistant headline.
    E.g. user: "What is MRR?" then "Break that down by region".
    """
    q = question.strip()
    if not history or not FOLLOW_UP_PATTERN.search(q):
        return q

    last_user = next((h["text"] for h in reversed(history) if h.get("role") == "user"), None)
    last_asst = next((h for h in reversed(history) if h.get("role") == "assistant"), None)
    headline = (last_asst or {}).get("headline") or (last_asst or {}).get("text")

    if "region" in q.lower():
        if last_user and "mrr" in last_user.lower():
            return "Show MRR by region"
        return f"{last_user or headline or 'Metrics'} by region"

    if "segment" in q.lower():
        return "Break down MRR by customer segment"

    if last_user:
        return f"{last_user} — follow-up: {q}"
    return q


def planner_context_from_history(history: list[dict[str, Any]]) -> str:
    if not history:
        return ""
    last = history[-1]
    if last.get("role") == "assistant" and last.get("mode") == "investigation":
        return "Prior turn was investigation mode; user may be drilling further."
    return ""
