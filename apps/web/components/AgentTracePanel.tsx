"use client";

import type { AgentTraceStep } from "@/lib/api";

export function AgentTracePanel({ trace }: { trace: AgentTraceStep[] }) {
  if (!trace?.length) return null;

  return (
    <details style={{ marginTop: 16 }}>
      <summary style={{ cursor: "pointer", fontWeight: 600 }}>
        Multi-agent trace ({trace.length} steps)
      </summary>
      <ol style={{ margin: "12px 0 0", paddingLeft: 20, fontSize: 13 }}>
        {trace.map((step, i) => (
          <li key={i} style={{ marginBottom: 8 }}>
            <strong>{step.agent}</strong> · {step.action}{" "}
            <span style={{ color: "var(--muted)" }}>({step.duration_ms} ms)</span>
            <div style={{ color: "var(--muted)", marginTop: 2 }}>{step.detail}</div>
          </li>
        ))}
      </ol>
    </details>
  );
}
