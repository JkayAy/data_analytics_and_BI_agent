import Link from "next/link";
import { SiteNav } from "@/components/SiteNav";

export default function AboutPage() {
  return (
    <>
      <SiteNav />
      <article style={{ maxWidth: 720, margin: "0 auto", padding: "0 20px 48px", lineHeight: 1.65 }}>
        <h1 style={{ fontSize: 28 }}>About InsightBridge</h1>
        <p>
          InsightBridge is an <strong>enterprise-style multi-agent analytics platform</strong> (Phase E1
          shipped). Eight specialist agents collaborate under a LangGraph orchestrator to deliver metrics,
          breakdowns, and investigations with visible SQL and audit trails.
        </p>

        <h2>Agent team</h2>
        <ul>
          <li>Planner — intent and investigation mode</li>
          <li>SQL Specialist — semantic-layer queries</li>
          <li>Governance — deterministic sqlglot policies</li>
          <li>Executor — warehouse runs</li>
          <li>Investigation — follow-up driver queries</li>
          <li>Analyst — executive narrative</li>
          <li>Visualization — charts</li>
          <li>QA Critic — quality gate</li>
        </ul>
        <p>
          See <Link href="/">Chat</Link> agent trace after each ask, or <code>GET /v1/agent/capabilities</code> on
          the API.
        </p>

        <h2>Design decisions</h2>
        <ol>
          <li>
            <strong>Validate before execute</strong> — sqlglot parses and blocks DML/DDL; the warehouse should still
            use a read-only role in production.
          </li>
          <li>
            <strong>Demo mode without API keys</strong> — curated pattern matching so recruiters can try the live demo
            without OpenAI spend.
          </li>
          <li>
            <strong>Single Postgres</strong> — demo analytics schema plus app metadata; keeps deploy cost low on
            Railway.
          </li>
          <li>
            <strong>Charts from heuristics</strong> — infer line/bar/metric from result shape; good enough for exec
            summaries in v1.
          </li>
        </ol>

        <h2>Enterprise roadmap</h2>
        <p>
          Phases E2–E6 (memory, connectors, SSO, Slack) are documented in{" "}
          <code>docs/ENTERPRISE_ROADMAP.md</code> in the repository. v0.3 is built for{" "}
          <strong>local testing and employer demos</strong>, not full Fortune 500 rollout yet.
        </p>

        <h2>Links</h2>
        <ul>
          <li>
            <a href="https://github.com/JkayAy/data_analytics_and_BI_agent">GitHub repository</a>
          </li>
          <li>Architecture: see repo <code>docs/ARCHITECTURE.md</code></li>
          <li>Deploy: see <code>docs/DEPLOY.md</code></li>
        </ul>
      </article>
    </>
  );
}
