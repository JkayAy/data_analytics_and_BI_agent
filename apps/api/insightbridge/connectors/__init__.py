"""Warehouse connectors — Postgres, BigQuery, Snowflake."""

from insightbridge.connectors.registry import get_active_connector, get_connector

__all__ = ["get_active_connector", "get_connector"]
