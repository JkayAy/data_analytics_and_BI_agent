# Agent Roster

## Planner Agent

**Goal:** Classify the business question and choose execution mode.

**Outputs (JSON):**

```json
{
  "intent": "metric|breakdown|trend|investigation",
  "mode": "standard|investigation",
  "plan_steps": ["Compute active MRR", "Compare regions if investigation"],
  "reasoning": "one sentence"
}
```

**Demo fallback:** Regex on `why`, `root cause`, `driver`, `decline` → `investigation`.

---

## SQL Specialist Agent

**Goal:** Produce one PostgreSQL `SELECT` aligned with `packages/semantic-layer/metrics.yaml`.

**Tools:** Semantic layer context string.

**Demo fallback:** `demo_sql.try_demo_sql()`.

---

## Governance Agent (deterministic)

**Goal:** Block unsafe SQL before execution.

**Implementation:** `sql_validator.validate_sql`, `ensure_limit`.

**Not LLM-powered** — this is intentional for enterprise trust.

---

## Executor Agent (deterministic)

**Goal:** Run query against warehouse; return rows + timing.

**Implementation:** `warehouse.execute_query`.

---

## Investigation Agent

**Goal:** When `mode=investigation`, run **additional** diagnostic queries (max 2 in E1).

**Demo behavior:**

- After primary MRR/churn question → auto-run regional or segment breakdown
- Merge findings into `investigation_runs` for Analyst

**LLM behavior:** Propose follow-up SQL based on primary result sample.

---

## Analyst Agent

**Goal:** Executive summary — headline, bullets, caveats, suggested follow-ups.

**Uses:** Primary + investigation results.

---

## Visualization Agent (deterministic)

**Goal:** Infer chart spec (`metric`, `line`, `bar`, `table`).

**Implementation:** `charts.infer_chart_spec`.

---

## QA Critic Agent

**Goal:** Block nonsensical answers (empty results without explanation, missing SQL, failed validation).

**Demo heuristic:** Pass if `status=success` and (`row_count > 0` or question allows empty).

**LLM:** JSON `{ "passed": true, "notes": "..." }`.

---

## Orchestrator

**Implementation:** `insightbridge.multi_agent.graph.run_multi_agent()`

**Entry:** `run_agent()` in `agent.py` delegates here when `MULTI_AGENT_ENABLED=true` (default).
