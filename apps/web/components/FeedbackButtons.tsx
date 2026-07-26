"use client";

import { useState } from "react";
import { submitFeedback } from "@/lib/api";

export function FeedbackButtons({ queryRunId }: { queryRunId: string }) {
  const [sent, setSent] = useState<-1 | 1 | null>(null);
  const [loading, setLoading] = useState(false);

  async function vote(rating: -1 | 1) {
    setLoading(true);
    try {
      await submitFeedback(queryRunId, rating);
      setSent(rating);
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }

  if (sent !== null) {
    return (
      <span style={{ fontSize: 13, color: "var(--muted)" }}>
        Thanks for the feedback{sent === 1 ? " 👍" : " 👎"}
      </span>
    );
  }

  return (
    <div style={{ display: "flex", gap: 8, alignItems: "center", marginTop: 12 }}>
      <span style={{ fontSize: 13, color: "var(--muted)" }}>Helpful?</span>
      <button type="button" disabled={loading} style={btnStyle} onClick={() => vote(1)}>
        Yes
      </button>
      <button type="button" disabled={loading} style={btnStyle} onClick={() => vote(-1)}>
        No
      </button>
    </div>
  );
}

const btnStyle: React.CSSProperties = {
  padding: "4px 10px",
  fontSize: 13,
  borderRadius: 6,
  border: "1px solid var(--border)",
  background: "#fff",
  cursor: "pointer",
};
