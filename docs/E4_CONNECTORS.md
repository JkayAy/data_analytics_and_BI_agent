# Phase E4 — Warehouse Connectors ✅

## Status

| Connector | Status | Module |
|-----------|--------|--------|
| **PostgreSQL** | ✅ Production-ready (local Docker) | `connectors/postgres.py` |
| **BigQuery** | ✅ Implemented (requires GCP creds) | `connectors/bigquery.py` |
| **Snowflake** | ✅ Implemented (requires account creds) | `connectors/snowflake.py` |

## Connection manager

Table: `app.connections` — stores dialect + `config_json` (encrypt at rest in E5).

| API | Description |
|-----|-------------|
| `GET /v1/connections` | List connections (secrets redacted) |
| `POST /v1/connections` | Create connection |
| `POST /v1/connections/{id}/activate` | Set active warehouse |
| `POST /v1/connections/{id}/test` | Run connectivity test |

Active connection is used by **Executor** via `warehouse.execute_query()` → `get_active_connector()`.

## Local Docker

```powershell
.\scripts\migrate-docker.ps1
```

Default active connection: **Local Docker Postgres** → `localhost:5432`.

## Config examples

**Postgres**

```json
{"url": "postgresql://insight:insight@localhost:5432/insightbridge"}
```

**BigQuery**

```json
{
  "project_id": "my-gcp-project",
  "dataset": "analytics",
  "credentials_path": "/path/to/service-account.json"
}
```

**Snowflake**

```json
{
  "account": "xy12345",
  "user": "READONLY_USER",
  "password": "...",
  "warehouse": "COMPUTE_WH",
  "database": "ANALYTICS",
  "schema": "ANALYTICS",
  "role": "READONLY"
}
```

## Governance

SQL validation dialect follows active connector: `postgres` | `bigquery` | `snowflake` (sqlglot).

Semantic layer `allowed_schemas` maps to Postgres schemas or BigQuery datasets.

## Dependencies

```bash
pip install google-cloud-bigquery snowflake-connector-python
```

Included in `apps/api/requirements.txt`.
