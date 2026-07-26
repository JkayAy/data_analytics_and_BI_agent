from __future__ import annotations

import json
import time
from typing import Any

from insightbridge.sql_validator import ensure_limit, mask_pii_columns, validate_sql


class ConnectorExecutionError(Exception):
    def __init__(self, message: str, code: str = "connector_error"):
        super().__init__(message)
        self.code = code


class BigQueryConnector:
    """Read-only BigQuery. Requires google-cloud-bigquery and ADC or service account JSON path."""

    def __init__(self, config: dict[str, Any]):
        self.project_id = config.get("project_id")
        self.default_dataset = config.get("dataset") or config.get("default_dataset")
        self.credentials_path = config.get("credentials_path")
        if not self.project_id:
            raise ValueError("BigQuery config requires 'project_id'")

    def dialect(self) -> str:
        return "bigquery"

    def _client(self):
        try:
            from google.cloud import bigquery
            from google.oauth2 import service_account
        except ImportError as exc:
            raise ConnectorExecutionError(
                "Install google-cloud-bigquery to use BigQuery connector",
                "missing_dependency",
            ) from exc

        if self.credentials_path:
            creds = service_account.Credentials.from_service_account_file(self.credentials_path)
            return bigquery.Client(project=self.project_id, credentials=creds)
        return bigquery.Client(project=self.project_id)

    def test(self) -> str:
        client = self._client()
        job = client.query("SELECT 1 AS ok")
        list(job.result(max_results=1))
        return f"BigQuery OK (project={self.project_id})"

    def execute_read_only(
        self,
        sql: str,
        *,
        allowed_schemas: set[str],
        row_limit: int,
        timeout_seconds: int,
        pii_columns: set[str] | None = None,
    ) -> tuple[list[dict[str, Any]], list[str], int]:
        # allowed_schemas maps to BigQuery datasets
        validated = validate_sql(sql, allowed_schemas, read_dialect="bigquery")
        bounded = ensure_limit(validated, row_limit)
        start = time.perf_counter()
        try:
            client = self._client()
            job_config = client._default_query_job_config if hasattr(client, "_default_query_job_config") else None
            from google.cloud import bigquery

            cfg = bigquery.QueryJobConfig(
                maximum_bytes_billed=10_000_000_000,
                use_query_cache=True,
            )
            if self.default_dataset:
                cfg.default_dataset = f"{self.project_id}.{self.default_dataset}"
            job = client.query(bounded, job_config=cfg, timeout=timeout_seconds)
            rows_iter = job.result(max_results=row_limit)
            rows = [dict(r.items()) for r in rows_iter]
            columns = [field.name for field in rows_iter.schema] if rows_iter.schema else (list(rows[0].keys()) if rows else [])
        except Exception as exc:
            raise ConnectorExecutionError(str(exc), "bq_error") from exc

        duration_ms = int((time.perf_counter() - start) * 1000)
        return mask_pii_columns(rows, pii_columns or set()), columns, duration_ms
