# Deploy InsightBridge (portfolio demo)

## Option A — Local (recruiters clone & run)

1. Start Docker Desktop → `docker compose up -d`
2. API + web per [README](../README.md)
3. Record a 90s Loom of “MRR by region” and embed in README

## Option B — Vercel + Railway (free tier friendly)

### Database (Railway Postgres)

1. Create Postgres service.
2. Connect with `psql` or Railway query tab.
3. Run scripts in order:
   - `infra/seed/01_schema.sql`
   - `infra/seed/02_data.sql`
   - `infra/seed/03_migrate.sql` (safe if already on latest schema)

### API (Railway)

1. New service → deploy from repo.
2. Set **Root Directory** to repository root (for Dockerfile) or use `apps/api/Dockerfile` with build context = repo root:
   - Dockerfile path: `apps/api/Dockerfile`
3. Environment variables:
   - `DATABASE_URL` = Railway Postgres URL
   - `CORS_ORIGINS` = `https://YOUR-APP.vercel.app`
   - `OPENAI_API_KEY` = optional
   - `API_KEY` = optional (set matching `NEXT_PUBLIC_API_KEY` on Vercel)
   - `SEMANTIC_LAYER_PATH` = `/packages/semantic-layer/metrics.yaml` (already set in Dockerfile)
4. Generate domain → note `https://xxx.up.railway.app`

### Web (Vercel)

1. Import GitHub repo.
2. **Root Directory:** `apps/web`
3. Environment: `NEXT_PUBLIC_API_URL=https://xxx.up.railway.app`
4. Optional: `NEXT_PUBLIC_GITHUB_URL`, `NEXT_PUBLIC_API_KEY` (if Railway `API_KEY` set), `DEMO_ACCESS_PASSWORD`
5. Deploy.

### Smoke test

```bash
curl https://xxx.up.railway.app/health
curl -X POST https://xxx.up.railway.app/v1/ask \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"What is our total MRR?\"}"
```

## GitHub polish checklist

- [ ] Pin repository on profile
- [ ] Topics: `text-to-sql`, `fastapi`, `nextjs`, `business-intelligence`, `langchain-alternative`
- [ ] README hero GIF or Loom link
- [ ] CI badge: `![CI](https://github.com/USER/insightbridge/actions/workflows/ci.yml/badge.svg)`
- [ ] Resume + LinkedIn link to live demo

## Security note for public demo

Use the **seed dataset only**. Do not expose production warehouse credentials. Optional: basic auth on Vercel via middleware if you see abuse.
