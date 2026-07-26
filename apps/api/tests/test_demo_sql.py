import pytest

from insightbridge.demo_sql import try_demo_sql


@pytest.mark.parametrize(
    "question",
    [
        "What is our MRR?",
        "Show monthly recurring revenue",
        "MRR by region",
        "What is our churn rate?",
        "Top customers by MRR",
        "Orders by month",
        "Revenue by segment",
    ],
)
def test_demo_patterns(question: str):
    match = try_demo_sql(question)
    assert match is not None
    assert "SELECT" in match.sql.upper()
    assert "analytics." in match.sql.lower()
