from insightbridge.multi_agent.investigation_engine import rank_drivers


def test_rank_drivers_orders_by_value():
    runs = [
        {
            "purpose": "by region",
            "sql": "SELECT 1",
            "columns": ["region", "mrr_usd"],
            "preview": [
                {"region": "APAC", "mrr_usd": 100},
                {"region": "Europe", "mrr_usd": 500},
            ],
        }
    ]
    ranked = rank_drivers(runs)
    assert ranked[0]["driver"] == "Europe"
    assert ranked[0]["rank"] == 1
