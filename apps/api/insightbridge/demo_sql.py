from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class DemoMatch:
    sql: str
    assumptions: list[str]


def try_demo_sql(question: str) -> DemoMatch | None:
    """Rule-based SQL for portfolio demo when no LLM key is configured."""
    q = question.lower().strip()

    # More specific patterns first — generic MRR total is last.
    if _matches(q, r"by region", r"per region", r"each region", r"across regions") and _matches(
        q, r"revenue", r"mrr", r"subscription"
    ):
        return DemoMatch(
            sql="""
SELECT c.region,
       ROUND(SUM(s.mrr_cents) FILTER (WHERE s.status = 'active') / 100.0, 2) AS mrr_usd
FROM analytics.customers c
JOIN analytics.subscriptions s ON s.customer_id = c.id
GROUP BY c.region
ORDER BY mrr_usd DESC
""".strip(),
            assumptions=["Active subscriptions only", "Joined customers for region"],
        )

    if _matches(q, r"top", r"best", r"highest") and _matches(q, r"customer", r"clients"):
        return DemoMatch(
            sql="""
SELECT c.name, c.region, ROUND(SUM(s.mrr_cents) / 100.0, 2) AS total_mrr_usd
FROM analytics.customers c
JOIN analytics.subscriptions s ON s.customer_id = c.id
WHERE s.status = 'active'
GROUP BY c.id, c.name, c.region
ORDER BY total_mrr_usd DESC
LIMIT 10
""".strip(),
            assumptions=["Ranked by active MRR", "Customer names masked in API if PII policy applies"],
        )

    if _matches(q, r"churn", r"cancelled", r"canceled"):
        return DemoMatch(
            sql="""
SELECT COUNT(*) FILTER (WHERE status = 'cancelled') AS churned,
       COUNT(*) FILTER (WHERE status = 'active') AS active,
       ROUND(
         100.0 * COUNT(*) FILTER (WHERE status = 'cancelled')
         / NULLIF(COUNT(*), 0),
         2
       ) AS churn_pct
FROM analytics.subscriptions
""".strip(),
            assumptions=["Churn % = cancelled / all subscriptions in dataset"],
        )

    if _matches(q, r"order", r"orders", r"one-time", r"bookings"):
        if _matches(q, r"month", r"over time", r"trend", r"by month"):
            return DemoMatch(
                sql="""
SELECT DATE_TRUNC('month', o.order_date)::date AS month,
       ROUND(SUM(o.amount_cents) / 100.0, 2) AS order_revenue_usd
FROM analytics.orders o
GROUP BY 1
ORDER BY 1
""".strip(),
                assumptions=["One-time order revenue, not MRR", "Grouped by calendar month"],
            )
        return DemoMatch(
            sql="""
SELECT o.product_category,
       ROUND(SUM(o.amount_cents) / 100.0, 2) AS revenue_usd,
       COUNT(*) AS order_count
FROM analytics.orders o
GROUP BY o.product_category
ORDER BY revenue_usd DESC
""".strip(),
            assumptions=["One-time orders only"],
        )

    if _matches(q, r"segment"):
        return DemoMatch(
            sql="""
SELECT c.segment,
       COUNT(DISTINCT c.id) AS customers,
       ROUND(SUM(s.mrr_cents) FILTER (WHERE s.status = 'active') / 100.0, 2) AS mrr_usd
FROM analytics.customers c
LEFT JOIN analytics.subscriptions s ON s.customer_id = c.id
GROUP BY c.segment
ORDER BY mrr_usd DESC NULLS LAST
""".strip(),
            assumptions=["Includes customers with no subscription via LEFT JOIN"],
        )

    if _matches(q, r"plan"):
        return DemoMatch(
            sql="""
SELECT s.plan,
       COUNT(*) FILTER (WHERE s.status = 'active') AS active_count,
       ROUND(SUM(s.mrr_cents) FILTER (WHERE s.status = 'active') / 100.0, 2) AS mrr_usd
FROM analytics.subscriptions s
GROUP BY s.plan
ORDER BY mrr_usd DESC
""".strip(),
            assumptions=["Active subscriptions by plan tier"],
        )

    if _matches(q, r"how many", r"count", r"number of") and _matches(q, r"customer"):
        return DemoMatch(
            sql="""
SELECT COUNT(*) AS customer_count FROM analytics.customers
""".strip(),
            assumptions=["Total customers in demo dataset"],
        )

    if _matches(q, r"\bmrr\b", r"recurring revenue", r"monthly revenue"):
        return DemoMatch(
            sql="""
SELECT ROUND(SUM(s.mrr_cents) FILTER (WHERE s.status = 'active') / 100.0, 2) AS mrr_usd
FROM analytics.subscriptions s
""".strip(),
            assumptions=["MRR = sum of active subscription MRR in USD", "Excludes one-time order revenue"],
        )

    return None


def _matches(q: str, *patterns: str) -> bool:
    return any(re.search(p, q) for p in patterns)
