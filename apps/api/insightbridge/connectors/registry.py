from __future__ import annotations

from typing import Any

from insightbridge.config import settings
from insightbridge.connectors.bigquery import BigQueryConnector
from insightbridge.connectors.postgres import PostgresConnector
from insightbridge.connectors.snowflake import SnowflakeConnector


def get_connector(dialect: str, config: dict[str, Any]):
    d = dialect.lower()
    if d == "postgres":
        return PostgresConnector(config)
    if d == "bigquery":
        return BigQueryConnector(config)
    if d == "snowflake":
        return SnowflakeConnector(config)
    raise ValueError(f"Unsupported dialect: {dialect}")


def get_active_connector():
    """Resolve connector from DB active connection or env fallback."""
    from insightbridge.db_connections import get_active_connection_record
    from insightbridge.request_context import current_auth

    ctx = current_auth()
    org_id = ctx.org_id if ctx else None
    record = get_active_connection_record(org_id)
    if record:
        config = dict(record["config_json"])
        if record["dialect"] == "postgres" and config.get("url"):
            config["url"] = _normalize_postgres_url(config["url"])
        return get_connector(record["dialect"], config), record

    # Fallback: local DATABASE_URL postgres (host docker vs localhost)
    url = settings.database_url
    connector = PostgresConnector({"url": url})
    fallback = {
        "id": None,
        "name": "Env DATABASE_URL",
        "dialect": "postgres",
        "config_json": {"url": url},
        "is_active": True,
    }
    return connector, fallback


def _normalize_postgres_url(url: str) -> str:
    """Docker seed uses host `db`; API on host uses localhost."""
    return url.replace("@db:5432", "@localhost:5432").replace("@db/", "@localhost/")
