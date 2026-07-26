"use client";

import { useCallback, useEffect, useState } from "react";
import { AgentTracePanel } from "@/components/AgentTracePanel";
import { ChartView } from "@/components/ChartView";
import { FeedbackButtons } from "@/components/FeedbackButtons";
import { SiteNav } from "@/components/SiteNav";
import {
  askQuestion,
  createConversation,
  fetchHealth,
  type AssistantMessage,
} from "@/lib/api";

const SUGGESTIONS = [
  "What is our total MRR?",
  "Show MRR by region",
  "What is our churn rate?",
  "Top 10 customers by MRR",
  "Order revenue by month",
  "Break down MRR by customer segment",
];

type ChatItem =
  | { role: "user"; text: string }
  | { role: "assistant"; content: AssistantMessage };

export default function ChatPage() {
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [demoMode, setDemoMode] = useState<boolean | null>(null);
  const [items, setItems] = useState<ChatItem[]>([]);

  useEffect(() => {
    fetchHealth().then((h) => setDemoMode(h?.demo_mode ?? null));
    createConversation("Portfolio demo")
      .then((c) => setConversationId(c.id))
      .catch((e) => setError(String(e)));
  }, []);

  const send = useCallback(
    async (text: string) => {
      if (!conversationId || !text.trim()) return;
      setError(null);
      setLoading(true);
      setItems((prev) => [...prev, { role: "user", text: text.trim() }]);
      setInput("");
      try {
        const res = await askQuestion(conversationId, text.trim());
        const content = res.assistant_message.content;
        if (!content.query_run_id && res.query_run_id) {
          content.query_run_id = res.query_run_id;
        }
        setItems((prev) => [...prev, { role: "assistant", content }]);
      } catch (e) {
        setError(String(e));
      } finally {
        setLoading(false);
      }
    },
    [conversationId],
  );

  return (
    <>
      <SiteNav />
      <div style={pageStyle}>
      <header style={headerStyle}>
        <div>
          <h1 style={{ margin: 0, fontSize: 22 }}>Ask your data</h1>
          <p style={{ margin: "4px 0 0", color: "var(--muted)", fontSize: 14 }}>
            Natural language → validated SQL → insights & charts
          </p>
        </div>
        <div style={{ textAlign: "right", fontSize: 13, color: "var(--muted)" }}>
          {demoMode === true && (
            <span style={badgeStyle}>Demo mode (no API key — curated questions)</span>
          )}
          {demoMode === false && <span style={badgeLiveStyle}>LLM + multi-agent</span>}
          <div style={{ marginTop: 6 }}>Try investigation: &quot;Why is MRR uneven across regions?&quot;</div>
        </div>
      </header>

      <main className="ib-main-grid" style={mainStyle}>
        <section style={chatPanelStyle}>
          <div style={messagesStyle}>
            {items.length === 0 && (
              <div style={emptyStyle}>
                <p>Ask a business question in plain English.</p>
                <div style={chipsWrap}>
                  {SUGGESTIONS.map((s) => (
                    <button key={s} type="button" style={chipStyle} onClick={() => send(s)} disabled={loading}>
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {items.map((item, idx) =>
              item.role === "user" ? (
                <div key={idx} style={userBubbleStyle}>
                  {item.text}
                </div>
              ) : (
                <AssistantBlock key={idx} content={item.content} onFollowUp={send} />
              ),
            )}
            {loading && <div style={loadingStyle}>Generating SQL → running query → summarizing…</div>}
            {error && <div style={errorStyle}>{error}</div>}
          </div>

          <form
            style={formStyle}
            onSubmit={(e) => {
              e.preventDefault();
              send(input);
            }}
          >
            <input
              style={inputStyle}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="e.g. What is our MRR by region?"
              disabled={loading || !conversationId}
            />
            <button type="submit" style={btnPrimary} disabled={loading || !input.trim() || !conversationId}>
              Ask
            </button>
          </form>
        </section>

        <aside style={asideStyle}>
          <h2 style={asideTitle}>How it works</h2>
          <ol style={{ paddingLeft: 18, margin: 0, fontSize: 14, lineHeight: 1.6 }}>
            <li>Semantic layer defines metrics & allowed schemas</li>
            <li>Agent generates SQL (LLM or demo rules)</li>
            <li>sqlglot validates read-only SELECT + LIMIT</li>
            <li>Postgres executes · results profiled · chart inferred</li>
            <li>Audit row stored in app.query_runs</li>
          </ol>
          <p style={{ fontSize: 13, color: "var(--muted)", marginTop: 16 }}>
            Built for portfolio / interviews — see README for architecture and local setup.
          </p>
        </aside>
      </main>
      </div>
    </>
  );
}

function AssistantBlock({
  content,
  onFollowUp,
}: {
  content: AssistantMessage;
  onFollowUp: (q: string) => void;
}) {
  const ok = content.status === "success" || content.status === "success_with_warnings";
  return (
    <div style={assistantBubbleStyle}>
      {(content.mode || content.intent) && (
        <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 8 }}>
          Mode: {content.mode ?? "standard"} · Intent: {content.intent ?? "—"}
          {content.plan_steps?.length ? ` · Plan: ${content.plan_steps.join(" → ")}` : ""}
        </div>
      )}
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
        <strong>{content.insight?.headline || content.text}</strong>
        {ok && (
          <span style={{ fontSize: 12, color: "var(--muted)" }}>
            {content.row_count} rows · {content.duration_ms} ms
            {content.sql_source ? ` · ${content.sql_source}` : ""}
          </span>
        )}
      </div>

      {content.insight?.bullets?.length > 0 && (
        <ul style={{ margin: "12px 0", paddingLeft: 20 }}>
          {content.insight.bullets.map((b, i) => (
            <li key={i} style={{ marginBottom: 4 }}>
              {b}
            </li>
          ))}
        </ul>
      )}

      {content.chart_spec && (
        <div style={{ marginTop: 16 }}>
          <ChartView spec={content.chart_spec} />
        </div>
      )}

      {content.sql && (
        <details style={{ marginTop: 16 }}>
          <summary style={{ cursor: "pointer", fontWeight: 600 }}>View SQL</summary>
          <pre style={sqlPreStyle}>{content.sql}</pre>
        </details>
      )}

      {content.insight?.caveats?.length > 0 && (
        <p style={{ fontSize: 13, color: "var(--muted)", marginTop: 12 }}>
          Caveats: {content.insight.caveats.join(" · ")}
        </p>
      )}

      {content.insight?.follow_ups?.length > 0 && (
        <div style={{ marginTop: 12, display: "flex", flexWrap: "wrap", gap: 8 }}>
          {content.insight.follow_ups.slice(0, 3).map((f) => (
            <button key={f} type="button" style={chipStyle} onClick={() => onFollowUp(f)}>
              {f}
            </button>
          ))}
        </div>
      )}

      {content.resolved_question && content.resolved_question !== content.insight?.headline && (
        <p style={{ fontSize: 12, color: "var(--muted)", marginTop: 8 }}>
          Resolved ask: {content.resolved_question}
        </p>
      )}

      {content.driver_rankings && content.driver_rankings.length > 0 && (
        <div style={{ marginTop: 12 }}>
          <strong style={{ fontSize: 14 }}>Ranked drivers</strong>
          <ol style={{ margin: "8px 0 0", paddingLeft: 20, fontSize: 13 }}>
            {content.driver_rankings.map((d) => (
              <li key={d.rank}>
                {d.driver} — {String(d.metric)}: {String(d.value)}
              </li>
            ))}
          </ol>
        </div>
      )}

      {content.agent_trace && content.agent_trace.length > 0 && (
        <AgentTracePanel trace={content.agent_trace} />
      )}

      {content.investigation_runs && content.investigation_runs.length > 0 && (
        <details style={{ marginTop: 12 }}>
          <summary style={{ cursor: "pointer", fontWeight: 600 }}>Investigation SQL</summary>
          {content.investigation_runs.map((run, i) => (
            <div key={i} style={{ marginTop: 8 }}>
              <div style={{ fontSize: 13, fontWeight: 600 }}>{run.purpose}</div>
              <pre style={sqlPreStyle}>{run.sql}</pre>
            </div>
          ))}
        </details>
      )}

      {!ok && content.error && <p style={{ color: "var(--error)" }}>{content.error}</p>}

      {content.query_run_id && (content.status === "success" || content.status === "success_with_warnings") && (
        <FeedbackButtons queryRunId={content.query_run_id} />
      )}
    </div>
  );
}

const pageStyle: React.CSSProperties = { maxWidth: 1200, margin: "0 auto", padding: "24px 20px 48px" };
const headerStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "flex-start",
  gap: 16,
  marginBottom: 24,
  flexWrap: "wrap",
};
const mainStyle: React.CSSProperties = { display: "grid", gridTemplateColumns: "1fr 280px", gap: 20 };
const chatPanelStyle: React.CSSProperties = {
  background: "var(--surface)",
  border: "1px solid var(--border)",
  borderRadius: "var(--radius)",
  display: "flex",
  flexDirection: "column",
  minHeight: 560,
};
const messagesStyle: React.CSSProperties = { flex: 1, padding: 20, overflowY: "auto" };
const formStyle: React.CSSProperties = {
  display: "flex",
  gap: 8,
  padding: 16,
  borderTop: "1px solid var(--border)",
};
const inputStyle: React.CSSProperties = {
  flex: 1,
  padding: "12px 14px",
  borderRadius: 8,
  border: "1px solid var(--border)",
  fontSize: 15,
};
const btnPrimary: React.CSSProperties = {
  padding: "12px 20px",
  background: "var(--primary)",
  color: "#fff",
  border: "none",
  borderRadius: 8,
  fontWeight: 600,
  cursor: "pointer",
};
const userBubbleStyle: React.CSSProperties = {
  alignSelf: "flex-end",
  maxWidth: "85%",
  background: "#eff6ff",
  padding: "10px 14px",
  borderRadius: 12,
  marginBottom: 12,
  marginLeft: "auto",
};
const assistantBubbleStyle: React.CSSProperties = {
  background: "#f8fafc",
  border: "1px solid var(--border)",
  padding: 16,
  borderRadius: 12,
  marginBottom: 16,
};
const emptyStyle: React.CSSProperties = { color: "var(--muted)", textAlign: "center", padding: "40px 12px" };
const chipsWrap: React.CSSProperties = { display: "flex", flexWrap: "wrap", gap: 8, justifyContent: "center", marginTop: 16 };
const chipStyle: React.CSSProperties = {
  padding: "8px 12px",
  borderRadius: 999,
  border: "1px solid var(--border)",
  background: "#fff",
  fontSize: 13,
  cursor: "pointer",
};
const loadingStyle: React.CSSProperties = { color: "var(--muted)", fontSize: 14, padding: 8 };
const errorStyle: React.CSSProperties = { color: "var(--error)", padding: 8 };
const asideStyle: React.CSSProperties = {
  background: "var(--surface)",
  border: "1px solid var(--border)",
  borderRadius: "var(--radius)",
  padding: 20,
  height: "fit-content",
};
const asideTitle: React.CSSProperties = { margin: "0 0 12px", fontSize: 16 };
const sqlPreStyle: React.CSSProperties = {
  background: "#0f172a",
  color: "#e2e8f0",
  padding: 14,
  borderRadius: 8,
  overflowX: "auto",
  fontSize: 12,
  lineHeight: 1.5,
};
const badgeStyle: React.CSSProperties = {
  display: "inline-block",
  background: "#fef3c7",
  color: "#92400e",
  padding: "4px 10px",
  borderRadius: 999,
  fontSize: 12,
};
const badgeLiveStyle: React.CSSProperties = {
  ...badgeStyle,
  background: "#dcfce7",
  color: "#166534",
};
