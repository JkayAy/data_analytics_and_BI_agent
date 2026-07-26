"use client";

import { useEffect, useState } from "react";
import { SiteNav } from "@/components/SiteNav";
import { API_URL, apiHeaders } from "@/lib/api";

type Channel = { id: string; name: string; channel_type: string; is_active: boolean };
type Schedule = {
  id: string;
  name: string;
  question: string;
  cron_expr: string;
  timezone: string;
  enabled: boolean;
  channel_name: string;
  last_status: string | null;
};

export default function SchedulesPage() {
  const [channels, setChannels] = useState<Channel[]>([]);
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [usage, setUsage] = useState<{ query_count: number; monthly_cap: number | null } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const orgId = "00000000-0000-4000-a000-000000000001";

  useEffect(() => {
    Promise.all([
      fetch(`${API_URL}/v1/delivery/channels`, { headers: apiHeaders() }).then((r) => r.json()),
      fetch(`${API_URL}/v1/schedules`, { headers: apiHeaders() }).then((r) => r.json()),
      fetch(`${API_URL}/v1/orgs/${orgId}/usage`, { headers: apiHeaders() }).then((r) => r.json()),
    ])
      .then(([ch, sch, u]) => {
        setChannels(ch.items || []);
        setSchedules(sch.items || []);
        setUsage(u);
      })
      .catch((e) => setError(String(e)));
  }, []);

  return (
    <>
      <SiteNav />
      <div style={{ maxWidth: 900, margin: "0 auto", padding: "0 20px 48px" }}>
        <h1>Delivery &amp; schedules (E6)</h1>
        <p style={{ color: "var(--muted)" }}>
          Push agent answers to Slack or Teams and run cron digests (e.g. Monday MRR).
        </p>
        {usage && (
          <p style={{ fontSize: 14 }}>
            Usage this month: <strong>{usage.query_count}</strong>
            {usage.monthly_cap != null && ` / ${usage.monthly_cap}`}
          </p>
        )}
        {error && <p style={{ color: "var(--error)" }}>{error}</p>}
        <h2>Channels</h2>
        <ul style={{ listStyle: "none", padding: 0 }}>
          {channels.map((c) => (
            <li key={c.id} style={card}>
              {c.name} · {c.channel_type} {c.is_active ? "" : "(inactive)"}
            </li>
          ))}
        </ul>
        <h2>Schedules</h2>
        <ul style={{ listStyle: "none", padding: 0 }}>
          {schedules.map((s) => (
            <li key={s.id} style={card}>
              <strong>{s.name}</strong> → {s.channel_name}
              <br />
              <code>{s.cron_expr}</code> ({s.timezone}) · {s.enabled ? "enabled" : "disabled"}
              {s.last_status && <span> · last: {s.last_status}</span>}
              <p style={{ margin: "8px 0 0", fontSize: 13 }}>{s.question}</p>
            </li>
          ))}
        </ul>
        <p style={{ fontSize: 13, color: "var(--muted)" }}>
          Configure via <code>POST /v1/delivery/channels</code> and <code>POST /v1/schedules</code>. See{" "}
          <code>docs/E6_DELIVERY.md</code>.
        </p>
      </div>
    </>
  );
}

const card: React.CSSProperties = {
  border: "1px solid var(--border)",
  borderRadius: 12,
  padding: 16,
  marginBottom: 12,
};
