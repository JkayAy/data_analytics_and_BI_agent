# README claim audit

Audit date: 2026-08-08. Method: run Quick Start steps, `pytest`, trace `multi_agent/`, grep E5/E6 routes.

## Quick Start results

| Step | Result |
|------|--------|
| `docker compose up -d` | **Works** when Docker Desktop is running |
| API venv + `pip install -r requirements.txt` | **Works** (`.venv` present) |
| `cp ../../.env.example ../../.env` | **Works** on Windows as `copy ..\..\.env.example ..\..\.env` |
| `uvicorn ... --port 8000` | **Works** (requires Postgres on `:5432`) |
| Web `npm install` + `npm run dev` | **Works** |
| README note "Run `03_migrate.sql` only" | **Incomplete** — E5/E6 need `07`, `08`; use `scripts/migrate-docker.ps1` |

## Demo mode (no `OPENAI_API_KEY`)

| Question | SQL correct | Rows | 8-agent trace | Investigation extras |
|----------|-------------|------|---------------|----------------------|
| What is our total MRR? | Yes | 1 | Yes | N/A |
| Show MRR by region | Yes (after pattern-order fix) | ≥2 | Yes | N/A |
| What is our churn rate? | Yes | 1 | Yes | N/A |
| Top 10 customers by MRR | Yes (after fix) | ≥2 | Yes | N/A |
| Order revenue by month | Yes | ≥1 | Yes | N/A |
| Why is MRR uneven across regions? | Yes | ≥2 | Yes | Yes (follow-up queries + drivers) |

## LLM mode

| Claim | Status |
|-------|--------|
| OpenAI SQL + planner + QA when key set | **Implemented in code** — **not verified** in this audit (no key in CI) |

## 8-agent pipeline

| Agent | Code | Wired in graph | Demo behavior |
|-------|------|----------------|---------------|
| Planner | `nodes.planner_node` | Yes | Rule-based in demo; LLM when key set |
| SQL Specialist | `nodes.sql_specialist_node` | Yes | `demo_sql` rules + semantic layer |
| Governance | `nodes.governance_node` | Yes | sqlglot (deterministic) |
| Executor | `nodes.executor_node` | Yes | Postgres via `warehouse.execute_query` |
| Investigation | `nodes.investigation_node` | Yes | Skips in standard mode; runs engine in investigation |
| Analyst | `nodes.analyst_node` | Yes | Rule-based insight synthesis |
| Visualization | `nodes.visualization_node` | Yes | `infer_chart_spec` |
| QA Critic | `nodes.qa_critic_node` | Yes | Heuristic in demo; LLM when key set |

None are empty stubs; Investigation skips intentionally when `mode != investigation`.

## Phase E5 / E6

| Claim | Evidence | Status |
|-------|----------|--------|
| Magic-link JWT | `auth_jwt.py`, `POST /v1/auth/magic-link`, `07_e5_tenancy.sql` | **Implemented** — needs migration + optional login |
| Org RBAC | `require_min_role`, `organization_members` | **Implemented** |
| Encrypted connections | `crypto.py`, `config_encrypted` column | **Implemented** |
| Audit CSV export | `GET /v1/orgs/{id}/audit/export.csv` | **Implemented** |
| Slack/Teams webhooks | `db_delivery.py`, `POST /v1/delivery/channels` | **Implemented** — needs real webhook URL |
| Scheduled reports | `scheduler_service.py`, `08_e6_delivery.sql` | **Implemented** — APScheduler in API lifespan |
| Usage caps | `usage.py`, `MONTHLY_QUERY_CAP` | **Implemented** |

Not "plan only" — but not covered by demo-flow tests; treat as optional modules.

## Bugs found and fixed

1. **demo_sql pattern order** — generic MRR matched before "by region" / "top customers".
2. **Decimal JSON** — API `/ask` crashed saving `result_preview` with Postgres `Decimal` values.

## Summary table

| README claim | Evidence | Status |
|--------------|----------|--------|
| 8-agent LangGraph pipeline | `graph.py`, `nodes.py`, tests | **Verified (demo)** |
| Demo mode example questions | `test_demo_flow.py` | **Verified** |
| Governance (sqlglot, allowlist, PII) | `sql_validator.py`, governance node | **Verified** |
| Audit log on ask | `test_demo_api_ask_creates_audit_row` | **Verified** |
| LLM mode | `llm.py`, OpenAI in planner/QA | **Unverified without key** |
| E5 tenancy | routes + migration | **Implemented, not e2e-tested here** |
| E6 delivery | routes + migration + scheduler | **Implemented, not e2e-tested here** |
| Live Vercel demo URL | placeholder in old README | **Removed** — not deployed |
