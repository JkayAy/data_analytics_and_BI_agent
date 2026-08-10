import pytest

from insightbridge.demo_sql import try_demo_sql


@pytest.mark.parametrize(
    "question,fragment",
    [
        ("What is our MRR?", "mrr_usd"),
        ("Show monthly recurring revenue", "mrr_usd"),
        ("MRR by region", "GROUP BY c.region"),
        ("Show MRR by region", "GROUP BY c.region"),
        ("Top 10 customers by MRR", "LIMIT 10"),
        ("What is our churn rate?", "churn_pct"),
        ("Orders by month", "DATE_TRUNC"),
        ("Revenue by segment", "segment"),
    ],
)
def test_demo_patterns(question: str, fragment: str):
    match = try_demo_sql(question)
    assert match is not None
    assert "SELECT" in match.sql.upper()
    assert "analytics." in match.sql.lower()
    assert fragment.lower() in match.sql.lower()
