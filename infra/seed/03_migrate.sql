-- Run on existing DBs created before feedback / question_text were added
ALTER TABLE app.query_runs ADD COLUMN IF NOT EXISTS question_text TEXT;

CREATE TABLE IF NOT EXISTS app.feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_run_id UUID NOT NULL REFERENCES app.query_runs(id) ON DELETE CASCADE,
    rating SMALLINT NOT NULL CHECK (rating IN (-1, 1)),
    comment TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (query_run_id)
);

CREATE INDEX IF NOT EXISTS idx_query_runs_created ON app.query_runs(created_at DESC);
