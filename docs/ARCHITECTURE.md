# InsightBridge Architecture (v0.3 — multi-agent)

## Overview

InsightBridge is an **enterprise-style multi-agent analytics platform** (local-first). Specialized agents collaborate under a **LangGraph** orchestrator (with sequential fallback) to answer BI questions with governance and auditability.

**Read next:** [ENTERPRISE_ROADMAP.md](./ENTERPRISE_ROADMAP.md) · [MULTI_AGENT_BLUEPRINT.md](./MULTI_AGENT_BLUEPRINT.md) · [AGENTS.md](./AGENTS.md)

## Multi-agent request lifecycle

1. **API** receives ask → `run_agent()` → `run_multi_agent()`.
2. **Planner** — intent + `standard` / `investigation` mode.
3. **SQL Specialist** — semantic-layer SQL (LLM or demo rules).
4. **Governance** — sqlglot validation (deterministic).
5. **Executor** — Postgres read-only query.
6. **Investigation** — optional follow-up SQL for driver analysis.
7. **Analyst** — executive narrative.
8. **Visualization** — chart spec.
9. **QA Critic** — quality gate; may loop back to SQL Specialist once.
10. **Persistence** — messages, `query_runs`, optional feedback; response includes **`agent_trace`**.

## Orchestration

| Component | Path |
|-----------|------|
| Graph | `apps/api/insightbridge/multi_agent/graph.py` |
| Agent nodes | `apps/api/insightbridge/multi_agent/nodes.py` |
| State | `apps/api/insightbridge/multi_agent/state.py` |
| Capabilities API | `GET /v1/agent/capabilities` |

Env: `MULTI_AGENT_USE_LANGGRAPH=true` (default). If LangGraph unavailable, sequential multi-agent still runs.

## Data model (Postgres)

| Schema | Purpose |
|--------|---------|
| `analytics.*` | Demo SaaS facts |
| `app.*` | Conversations, messages, query audit, feedback |

## Security posture

- Read-only SQL enforcement + schema allowlist + LIMIT + timeout.
- PII masking from semantic layer.
- Optional `API_KEY` on POST routes; optional Vercel demo password.
- **E5:** Magic-link JWT, org RBAC, org-scoped conversations/connections; Fernet-encrypted connection configs.
- **Not** a substitute for warehouse RBAC — use read-only DB roles in production ([WAREHOUSE_READONLY.md](./WAREHOUSE_READONLY.md)).

## Current vs roadmap

| Capability | Status |
|------------|--------|
| Multi-agent graph (E1) | Implemented |
| Conversation memory (E2) | Implemented |
| Investigation + drivers (E3) | Implemented |
| BQ / Snowflake (E4) | Implemented |
| SSO / tenancy (E5) | Implemented |
| Slack delivery (E6) | Implemented |
