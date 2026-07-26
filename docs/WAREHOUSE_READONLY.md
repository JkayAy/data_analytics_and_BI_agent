# Read-only warehouse roles (production)

InsightBridge enforces **SELECT-only** SQL in the app layer. Production deployments must also use **read-only credentials** at the warehouse.

## PostgreSQL

```sql
CREATE ROLE insightbridge_ro LOGIN PASSWORD '...';
GRANT USAGE ON SCHEMA analytics TO insightbridge_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO insightbridge_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA analytics GRANT SELECT ON TABLES TO insightbridge_ro;
```

Store URL in `app.connections` via API (encrypted when `ENCRYPTION_KEY` is set).

## BigQuery

- Service account with `roles/bigquery.dataViewer` on the dataset
- Optional: `bigquery.jobUser` for query jobs only

## Snowflake

- Role with `USAGE` on warehouse + `SELECT` on `ANALYTICS` schema
- No `WRITE` privileges

## App connection test

`POST /v1/connections/{id}/test` validates connectivity before activation.
