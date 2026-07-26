"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { SiteNav } from "@/components/SiteNav";

function GateForm() {
  const router = useRouter();
  const params = useSearchParams();
  const from = params.get("from") || "/";
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    const res = await fetch("/api/gate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password }),
    });
    setLoading(false);
    if (!res.ok) {
      setError("Incorrect password");
      return;
    }
    router.push(from);
    router.refresh();
  }

  return (
    <div style={{ maxWidth: 400, margin: "80px auto", padding: 20 }}>
      <h1 style={{ fontSize: 22 }}>Demo access</h1>
      <p style={{ color: "var(--muted)", fontSize: 14 }}>
        This public demo is password-protected. Ask the owner for access.
      </p>
      <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: 12, marginTop: 20 }}>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          style={inputStyle}
        />
        {error && <p style={{ color: "var(--error)", margin: 0 }}>{error}</p>}
        <button type="submit" disabled={loading} style={btnStyle}>
          Continue
        </button>
      </form>
    </div>
  );
}

export default function GatePage() {
  return (
    <>
      <SiteNav />
      <Suspense fallback={<p style={{ padding: 40 }}>Loading…</p>}>
        <GateForm />
      </Suspense>
    </>
  );
}

const inputStyle: React.CSSProperties = {
  padding: "12px 14px",
  borderRadius: 8,
  border: "1px solid var(--border)",
};
const btnStyle: React.CSSProperties = {
  padding: "12px 20px",
  background: "var(--primary)",
  color: "#fff",
  border: "none",
  borderRadius: 8,
  fontWeight: 600,
  cursor: "pointer",
};
