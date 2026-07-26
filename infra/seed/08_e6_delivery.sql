-- E6: Delivery channels (Slack/Teams), scheduled reports, usage metering

CREATE TABLE IF NOT EXISTS app.delivery_channels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    channel_type VARCHAR(20) NOT NULL CHECK (channel_type IN ('slack', 'teams')),
    webhook_url_encrypted TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_delivery_channels_org ON app.delivery_channels (org_id);

CREATE TABLE IF NOT EXISTS app.scheduled_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    delivery_channel_id UUID NOT NULL REFERENCES app.delivery_channels(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    question TEXT NOT NULL,
    cron_expr VARCHAR(100) NOT NULL DEFAULT '0 9 * * 1',
    timezone VARCHAR(64) NOT NULL DEFAULT 'UTC',
    enabled BOOLEAN NOT NULL DEFAULT true,
    last_run_at TIMESTAMPTZ,
    last_status VARCHAR(20),
    last_error TEXT,
    created_by UUID REFERENCES app.users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scheduled_reports_org ON app.scheduled_reports (org_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_reports_due ON app.scheduled_reports (enabled, last_run_at);

CREATE TABLE IF NOT EXISTS app.org_usage_monthly (
    org_id UUID NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    period_month DATE NOT NULL,
    query_count INT NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (org_id, period_month)
);

-- Demo: Monday 9am UTC scheduled MRR digest (disabled until webhook configured)
INSERT INTO app.delivery_channels (id, org_id, name, channel_type, webhook_url_encrypted, is_active)
SELECT
    '00000000-0000-4000-a000-000000000010'::uuid,
    '00000000-0000-4000-a000-000000000001'::uuid,
    'Demo Slack (configure webhook)',
    'slack',
    'plain:{"webhook_url":""}',
    false
WHERE NOT EXISTS (
    SELECT 1 FROM app.delivery_channels WHERE id = '00000000-0000-4000-a000-000000000010'::uuid
);

INSERT INTO app.scheduled_reports (
    id, org_id, delivery_channel_id, name, question, cron_expr, enabled, created_by
)
SELECT
    '00000000-0000-4000-a000-000000000011'::uuid,
    '00000000-0000-4000-a000-000000000001'::uuid,
    '00000000-0000-4000-a000-000000000010'::uuid,
    'Monday MRR digest',
    'What is our total MRR and MRR by region?',
    '0 9 * * 1',
    false,
    '00000000-0000-4000-a000-000000000002'::uuid
WHERE NOT EXISTS (
    SELECT 1 FROM app.scheduled_reports WHERE id = '00000000-0000-4000-a000-000000000011'::uuid
);
