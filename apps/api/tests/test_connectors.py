from insightbridge.connectors.registry import _normalize_postgres_url


def test_normalize_postgres_docker_host():
    url = "postgresql://insight:insight@db:5432/insightbridge"
    assert "@localhost:5432" in _normalize_postgres_url(url)
