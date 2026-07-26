# InsightBridge Enterprise Roadmap



**Vision:** Multi-agent analytics platform that compresses BI work from days to minutes — with governance suitable for real warehouses.



**Reality check:** No software replaces every analyst. The goal is **higher throughput and consistency** on repeatable BI tasks (metrics, breakdowns, trends, investigations), with humans owning metric definitions and high-stakes decisions.



---



## Phase map (build order)



| Phase | Name | Outcome | Status |

|-------|------|---------|--------|

| **E0** | Foundation | Postgres demo warehouse, semantic layer, API, web UI | **Done** |

| **E1** | Multi-agent core | LangGraph orchestration, specialist agents, local trace | **Done** |

| **E2** | Conversation memory | Thread history fed to planner/SQL agents | **Done** |

| **E3** | Investigation mode | Multi-query root-cause loops (≤5 queries, 120s budget), ranked drivers | **Done** |

| **E4** | Enterprise connectors | Postgres + BQ + Snowflake + connection manager API | **Done** |

| **E5** | Identity & tenancy | Orgs, RBAC, magic-link JWT, audit export | **Done** |

| **E6** | Delivery & ops | Slack/Teams, schedules, usage metering | **Done** |



---



## Phase E2 — Conversation memory ✅



- Load last N messages from `app.messages` on ask (`conversation_history_turns`)

- `expand_follow_up()` resolves “break down by region” using prior turns

- Planner + SQL Specialist receive history; `resolved_question` stored in `run_metadata`



**Test locally:** Ask “What is our total MRR?” then “Break that down by region” in the same chat.



---



## Phase E3 — Investigation mode ✅



- Planner sets `mode=investigation` for why/root-cause questions

- Investigation engine runs up to **5** queries within **120s** budget

- **Ranked drivers** in API + UI + analyst bullets



**Test locally:** *Why is MRR uneven across regions?*



---



## Phase E4 — Connectors ✅



See [E4_CONNECTORS.md](./E4_CONNECTORS.md).



---



## Phase E5 — Tenancy & compliance ✅



See [E5_TENANCY.md](./E5_TENANCY.md) and [WAREHOUSE_READONLY.md](./WAREHOUSE_READONLY.md).

- Magic-link JWT, org RBAC, org-scoped data
- Encrypted connection configs; audit CSV export



---



## Phase E6 — Production delivery ✅

See [E6_DELIVERY.md](./E6_DELIVERY.md).

- Slack/Teams webhook delivery, scheduled cron reports
- Slack slash command integration
- Monthly usage metering + optional caps



---



## Document index



- [MULTI_AGENT_BLUEPRINT.md](./MULTI_AGENT_BLUEPRINT.md)

- [AGENTS.md](./AGENTS.md)

- [ARCHITECTURE.md](./ARCHITECTURE.md)

- [E4_CONNECTORS.md](./E4_CONNECTORS.md)
- [E5_TENANCY.md](./E5_TENANCY.md)
- [E6_DELIVERY.md](./E6_DELIVERY.md)


