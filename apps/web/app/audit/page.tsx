"use client";

import { useEffect, useState } from "react";
import { SiteNav } from "@/components/SiteNav";
import { fetchAuditLog, type QueryRunAudit } from "@/lib/api";

export default function AuditPage() {
  const [items, setItems] = useState<QueryRunAudit[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAuditLog(100)
      .then((r) => setItems(r.items))
      .catch((e) => setError(String(e)));
  }, []);

  return (
    <>
      <SiteNav />
      <div style={{ maxWidth: 1200, margin: "0 auto", padding: "0 20px 48px" }}>
        <h1 style={{ fontSize: 24, marginBottom: 8 }}>Query audit log</h1>
        <p style={{ color: "var(--muted)", marginTop: 0, marginBottom: 24 }}>
          Every ask persists SQL, timing, and status — governance for conversational analytics.
        </p>
        {error && <p style={{ color: "var(--error)" }}>{error}</p>}
        <div style={{ overflowX: "auto", background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 12 }}>
          <table style={tableStyle}>
            <thead>
              <tr>
                <th style={thStyle}>When</th>
                <th style={thStyle}>Question</th>
                <th style={thStyle}>Status</th>
                <th style={thStyle}>Rows</th>
                <th style={thStyle}>Ms</th>
                <th style={thStyle}>Feedback</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 && !error && (
                <tr>
                  <td colSpan={6} style={{ ...tdStyle, color: "var(--muted)" }}>
                    No queries yet — ask something on the Chat page.
                  </td>
                </tr>
              )}
              {items.map((row) => (
                <tr key={row.id}>
                  <td style={tdStyle}>{new Date(row.created_at).toLocaleString()}</td>
                  <td style={tdStyle}>{row.question_text ?? "—"}</td>
                  <td style={tdStyle}>
                    <span style={row.status === "success" ? okBadge : errBadge}>{row.status}</span>
                  </td>
                  <td style={tdStyle}>{row.row_count ?? "—"}</td>
                  <td style={tdStyle}>{row.duration_ms ?? "—"}</td>
                  <td style={tdStyle}>
                    {row.feedback_rating === 1 ? "👍" : row.feedback_rating === -1 ? "👎" : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {items.map((row) => (
          <details key={`sql-${row.id}`} style={{ marginTop: 16 }}>
            <summary style={{ cursor: "pointer", fontWeight: 600 }}>
              SQL · {row.question_text?.slice(0, 60) ?? row.id}
            </summary>
            <pre style={preStyle}>{row.sql_text}</pre>
            {row.error_message && <p style={{ color: "var(--error)" }}>{row.error_message}</p>}
          </details>
        ))}
      </div>
    </>
  );
}

const tableStyle: React.CSSProperties = { width: "100%", borderCollapse: "collapse", fontSize: 13 };
const thStyle: React.CSSProperties = {
  textAlign: "left",
  padding: "10px 12px",
  borderBottom: "2px solid var(--border)",
  background: "#f1f5f9",
};
const tdStyle: React.CSSProperties = { padding: "10px 12px", borderBottom: "1px solid var(--border)", verticalAlign: "top" };
const preStyle: React.CSSProperties = {
  background: "#0f172a",
  color: "#e2e8f0",
  padding: 14,
  borderRadius: 8,
  overflowX: "auto",
  fontSize: 12,
};
const okBadge: React.CSSProperties = {
  background: "#dcfce7",
  color: "#166534",
  padding: "2px 8px",
  borderRadius: 999,
  fontSize: 12,
};
const errBadge: React.CSSProperties = {
  background: "#fee2e2",
  color: "#991b1b",
  padding: "2px 8px",
  borderRadius: 999,
  fontSize: 12,
};
