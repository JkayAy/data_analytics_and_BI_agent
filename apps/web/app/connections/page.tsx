"use client";

import { useEffect, useState } from "react";
import { SiteNav } from "@/components/SiteNav";
import { API_URL } from "@/lib/api";

type Connection = {
  id: string;
  name: string;
  dialect: string;
  is_active: boolean;
  config_json: Record<string, unknown>;
};

export default function ConnectionsPage() {
  const [items, setItems] = useState<Connection[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/v1/connections`)
      .then((r) => r.json())
      .then((d) => setItems(d.items || []))
      .catch((e) => setError(String(e)));
  }, []);

  return (
    <>
      <SiteNav />
      <div style={{ maxWidth: 900, margin: "0 auto", padding: "0 20px 48px" }}>
        <h1>Warehouse connections (E4)</h1>
        <p style={{ color: "var(--muted)" }}>
          Active connection is used by the Executor agent. Manage via API or activate below.
        </p>
        {error && <p style={{ color: "var(--error)" }}>{error}</p>}
        <ul style={{ listStyle: "none", padding: 0 }}>
          {items.map((c) => (
            <li
              key={c.id}
              style={{
                border: "1px solid var(--border)",
                borderRadius: 12,
                padding: 16,
                marginBottom: 12,
                background: c.is_active ? "#eff6ff" : "#fff",
              }}
            >
              <strong>{c.name}</strong> · {c.dialect}
              {c.is_active && <span style={{ marginLeft: 8, color: "var(--primary)" }}>(active)</span>}
              <pre style={{ fontSize: 12, marginTop: 8, overflow: "auto" }}>
                {JSON.stringify(c.config_json, null, 2)}
              </pre>
            </li>
          ))}
        </ul>
        <p style={{ fontSize: 13, color: "var(--muted)" }}>
          POST <code>/v1/connections</code> · POST <code>/v1/connections/&#123;id&#125;/test</code> · See{" "}
          <code>docs/E4_CONNECTORS.md</code>
        </p>
      </div>
    </>
  );
}
