-- Demo SaaS analytics schema (read-only queries in app)
CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE analytics.customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    region VARCHAR(50) NOT NULL,
    segment VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE analytics.subscriptions (
    id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES analytics.customers(id),
    plan VARCHAR(50) NOT NULL,
    mrr_cents INT NOT NULL,
    status VARCHAR(20) NOT NULL,
    started_at DATE NOT NULL,
    cancelled_at DATE
);

CREATE TABLE analytics.orders (
    id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES analytics.customers(id),
    amount_cents INT NOT NULL,
    order_date DATE NOT NULL,
    product_category VARCHAR(80) NOT NULL
);

CREATE INDEX idx_subscriptions_status ON analytics.subscriptions(status);
CREATE INDEX idx_orders_date ON analytics.orders(order_date);

-- App metadata (conversations, audit)
CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE app.conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE app.messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES app.conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE app.query_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID REFERENCES app.messages(id) ON DELETE SET NULL,
    question_text TEXT,
    sql_text TEXT NOT NULL,
    status VARCHAR(30) NOT NULL,
    row_count INT,
    duration_ms INT,
    error_message TEXT,
    result_preview JSONB,
    chart_spec JSONB,
    run_metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE app.feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_run_id UUID NOT NULL REFERENCES app.query_runs(id) ON DELETE CASCADE,
    rating SMALLINT NOT NULL CHECK (rating IN (-1, 1)),
    comment TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (query_run_id)
);

CREATE INDEX idx_messages_conversation ON app.messages(conversation_id);
CREATE INDEX idx_query_runs_created ON app.query_runs(created_at DESC);

-- E4: warehouse connections
CREATE TABLE app.connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    dialect VARCHAR(32) NOT NULL CHECK (dialect IN ('postgres', 'bigquery', 'snowflake')),
    config_json JSONB NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_connections_one_active ON app.connections (is_active) WHERE is_active = true;
