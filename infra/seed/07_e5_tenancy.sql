-- E5: Tenancy, auth, encrypted connection configs, audit events

CREATE TABLE IF NOT EXISTS app.organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(320) NOT NULL UNIQUE,
    name VARCHAR(200),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app.organization_members (
    org_id UUID NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES app.users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('owner', 'admin', 'member', 'viewer')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (org_id, user_id)
);

CREATE TABLE IF NOT EXISTS app.magic_link_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(320) NOT NULL,
    token_hash VARCHAR(128) NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app.audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES app.organizations(id) ON DELETE SET NULL,
    actor_user_id UUID REFERENCES app.users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    metadata_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE app.conversations ADD COLUMN IF NOT EXISTS org_id UUID REFERENCES app.organizations(id);
ALTER TABLE app.conversations ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES app.users(id);

ALTER TABLE app.connections ADD COLUMN IF NOT EXISTS org_id UUID REFERENCES app.organizations(id);
ALTER TABLE app.connections ADD COLUMN IF NOT EXISTS config_encrypted TEXT;

ALTER TABLE app.query_runs ADD COLUMN IF NOT EXISTS org_id UUID REFERENCES app.organizations(id);

DROP INDEX IF EXISTS app.idx_connections_one_active;
CREATE UNIQUE INDEX IF NOT EXISTS idx_connections_one_active_per_org
    ON app.connections (org_id) WHERE is_active = true;

INSERT INTO app.organizations (id, name, slug)
SELECT '00000000-0000-4000-a000-000000000001'::uuid, 'Demo Organization', 'demo'
WHERE NOT EXISTS (SELECT 1 FROM app.organizations WHERE slug = 'demo');

INSERT INTO app.users (id, email, name)
SELECT '00000000-0000-4000-a000-000000000002'::uuid, 'demo@insightbridge.local', 'Demo Admin'
WHERE NOT EXISTS (SELECT 1 FROM app.users WHERE email = 'demo@insightbridge.local');

INSERT INTO app.organization_members (org_id, user_id, role)
SELECT
    '00000000-0000-4000-a000-000000000001'::uuid,
    '00000000-0000-4000-a000-000000000002'::uuid,
    'owner'
WHERE NOT EXISTS (
    SELECT 1 FROM app.organization_members
    WHERE org_id = '00000000-0000-4000-a000-000000000001'::uuid
);

UPDATE app.connections
SET org_id = '00000000-0000-4000-a000-000000000001'::uuid
WHERE org_id IS NULL;

UPDATE app.conversations
SET org_id = '00000000-0000-4000-a000-000000000001'::uuid
WHERE org_id IS NULL;
