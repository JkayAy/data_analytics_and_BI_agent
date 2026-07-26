# Phase E5 — Tenancy & compliance

## Implemented

| Feature | Details |
|---------|---------|
| **Organizations & RBAC** | `owner`, `admin`, `member`, `viewer` via `app.organization_members` |
| **Magic-link auth** | `POST /v1/auth/magic-link`, `POST /v1/auth/verify` → JWT |
| **Org isolation** | Conversations, query runs, connections scoped by `org_id` |
| **Encrypted connections** | `config_encrypted` (Fernet) or dev `plain:` fallback |
| **Audit events** | `app.audit_events` + `log_audit()` on key actions |
| **CSV export** | `GET /v1/orgs/{org_id}/audit/export.csv` (admin+) |

## Local defaults

- `AUTH_REQUIRED=false` — API uses demo org/user without JWT (portfolio friendly)
- `AUTH_REQUIRED=true` — require `Authorization: Bearer` on protected routes
- Demo org id: `00000000-0000-4000-a000-000000000001`
- Demo user: `demo@insightbridge.local`

## Environment

```env
AUTH_REQUIRED=false
JWT_SECRET=change-me
ENCRYPTION_KEY=   # optional; generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
MAGIC_LINK_DEV_EXPOSE=true
```

## Web sign-in

`/login` → request magic link → verify token → JWT in `localStorage` as `insightbridge_token`.

## Read-only warehouse

See [WAREHOUSE_READONLY.md](./WAREHOUSE_READONLY.md) for DB role guidance (Postgres/BQ/Snowflake).

## Migration

```powershell
.\scripts\migrate-docker.ps1
```

Includes `07_e5_tenancy.sql`.

## Next

Enterprise roadmap E0–E6 is complete. Optional: Stripe billing, OIDC SSO, metric approval workflows.
