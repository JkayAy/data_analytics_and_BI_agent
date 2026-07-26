ALTER TABLE app.query_runs ADD COLUMN IF NOT EXISTS run_metadata JSONB;
