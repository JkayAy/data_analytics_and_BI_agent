-- E4: warehouse connection manager (local dev; encrypt in E5)
CREATE TABLE IF NOT EXISTS app.connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    dialect VARCHAR(32) NOT NULL CHECK (dialect IN ('postgres', 'bigquery', 'snowflake')),
    config_json JSONB NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_connections_one_active
    ON app.connections (is_active) WHERE is_active = true;

-- Default local Docker analytics warehouse
INSERT INTO app.connections (name, dialect, config_json, is_active)
SELECT
    'Local Docker Postgres',
    'postgres',
    '{"url": "postgresql://insight:insight@localhost:5432/insightbridge"}'::jsonb,
    true
WHERE NOT EXISTS (SELECT 1 FROM app.connections);
