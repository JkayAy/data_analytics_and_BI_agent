"use client";

import { useState } from "react";
import { SiteNav } from "@/components/SiteNav";
import { requestMagicLink, verifyMagicLink } from "@/lib/api";

export default function LoginPage() {
  const [email, setEmail] = useState("demo@insightbridge.local");
  const [token, setToken] = useState("");
  const [devToken, setDevToken] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);

  async function sendLink(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const res = await requestMagicLink(email);
      if (res.magic_link_token) {
        setDevToken(res.magic_link_token);
        setOk("Dev mode: copy the token below and verify.");
      } else {
        setOk("Magic link sent (configure email in production).");
      }
    } catch (err) {
      setError(String(err));
    }
  }

  async function verify(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const t = token || devToken;
    if (!t) return;
    try {
      const res = await verifyMagicLink(t);
      localStorage.setItem("insightbridge_token", res.access_token);
      setOk("Signed in. Go to Chat.");
      window.location.href = "/";
    } catch (err) {
      setError(String(err));
    }
  }

  return (
    <>
      <SiteNav />
      <div style={{ maxWidth: 440, margin: "40px auto", padding: 20 }}>
        <h1>Sign in (E5)</h1>
        <p style={{ color: "var(--muted)", fontSize: 14 }}>
          Magic-link auth for org isolation. Local dev exposes token in API response when{" "}
          <code>MAGIC_LINK_DEV_EXPOSE=true</code>.
        </p>
        <form onSubmit={sendLink} style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <input
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Email"
            style={{ padding: 12, borderRadius: 8, border: "1px solid var(--border)" }}
          />
          <button type="submit" style={btn}>
            Send magic link
          </button>
        </form>
        {devToken && (
          <p style={{ fontSize: 12, wordBreak: "break-all", marginTop: 12 }}>
            Dev token: <code>{devToken}</code>
          </p>
        )}
        <form onSubmit={verify} style={{ marginTop: 24, display: "flex", flexDirection: "column", gap: 10 }}>
          <input
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="Paste magic link token"
            style={{ padding: 12, borderRadius: 8, border: "1px solid var(--border)" }}
          />
          <button type="submit" style={btn}>
            Verify &amp; sign in
          </button>
        </form>
        {ok && <p style={{ color: "var(--success)", marginTop: 12 }}>{ok}</p>}
        {error && <p style={{ color: "var(--error)", marginTop: 12 }}>{error}</p>}
      </div>
    </>
  );
}

const btn: React.CSSProperties = {
  padding: "12px 16px",
  background: "var(--primary)",
  color: "#fff",
  border: "none",
  borderRadius: 8,
  fontWeight: 600,
  cursor: "pointer",
};
