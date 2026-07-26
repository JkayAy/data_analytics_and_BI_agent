from __future__ import annotations

from typing import Any

from insightbridge.agent import AgentResult


def _bullets(insight: dict[str, Any], limit: int = 5) -> list[str]:
    bullets = insight.get("bullets") or []
    return [str(b) for b in bullets[:limit]]


def format_slack_payload(result: AgentResult, *, title: str, question: str) -> dict[str, Any]:
    headline = (result.insight or {}).get("headline") or "InsightBridge report"
    blocks: list[dict[str, Any]] = [
        {"type": "header", "text": {"type": "plain_text", "text": title[:150]}},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Question:* {question}\n*Answer:* {headline}"},
        },
    ]
    for line in _bullets(result.insight or {}):
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"• {line}"}})
    if result.sql:
        sql_preview = result.sql if len(result.sql) < 800 else result.sql[:800] + "…"
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"```{sql_preview}```"},
            }
        )
    blocks.append(
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Status: *{result.status}* · Rows: {result.row_count} · {result.duration_ms}ms",
                }
            ],
        }
    )
    return {"text": headline, "blocks": blocks}


def format_teams_payload(result: AgentResult, *, title: str, question: str) -> dict[str, Any]:
    headline = (result.insight or {}).get("headline") or "InsightBridge report"
    facts = [
        {"title": "Question", "value": question[:200]},
        {"title": "Headline", "value": headline[:200]},
        {"title": "Status", "value": result.status},
        {"title": "Rows", "value": str(result.row_count)},
    ]
    for i, line in enumerate(_bullets(result.insight or {}, limit=3)):
        facts.append({"title": f"Insight {i + 1}", "value": line[:200]})
    return {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "summary": title,
        "themeColor": "0078D4" if result.status == "success" else "CC0000",
        "title": title,
        "sections": [{"facts": facts}],
    }


def format_slack_ephemeral(result: AgentResult, question: str) -> dict[str, Any]:
    headline = (result.insight or {}).get("headline") or "No headline"
    text = f"*Q:* {question}\n*A:* {headline}"
    for line in _bullets(result.insight or {}, limit=3):
        text += f"\n• {line}"
    if result.error:
        text += f"\n_Error:_ {result.error}"
    return {"response_type": "ephemeral", "text": text[:3000]}
