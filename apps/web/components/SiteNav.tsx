import Link from "next/link";

const GITHUB_URL = process.env.NEXT_PUBLIC_GITHUB_URL ?? "https://github.com/JkayAy/data_analytics_and_BI_agent";

export function SiteNav() {
  return (
    <nav style={navStyle}>
      <div style={innerStyle}>
        <Link href="/" style={brandStyle}>
          InsightBridge
        </Link>
        <div style={linksStyle}>
          <Link href="/" style={linkStyle}>
            Chat
          </Link>
          <Link href="/audit" style={linkStyle}>
            Audit log
          </Link>
          <Link href="/connections" style={linkStyle}>
            Connections
          </Link>
          <Link href="/schedules" style={linkStyle}>
            Schedules
          </Link>
          <Link href="/about" style={linkStyle}>
            About
          </Link>
          <Link href="/login" style={linkStyle}>
            Sign in
          </Link>
          <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer" style={linkStyle}>
            GitHub
          </a>
        </div>
      </div>
      <p style={taglineStyle}>Portfolio · Conversational BI agent</p>
    </nav>
  );
}

const navStyle: React.CSSProperties = {
  borderBottom: "1px solid var(--border)",
  background: "var(--surface)",
  marginBottom: 24,
};
const innerStyle: React.CSSProperties = {
  maxWidth: 1200,
  margin: "0 auto",
  padding: "16px 20px 8px",
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  flexWrap: "wrap",
  gap: 12,
};
const brandStyle: React.CSSProperties = {
  fontWeight: 700,
  fontSize: 18,
  color: "var(--text)",
  textDecoration: "none",
};
const linksStyle: React.CSSProperties = { display: "flex", gap: 16, flexWrap: "wrap" };
const linkStyle: React.CSSProperties = {
  color: "var(--primary)",
  textDecoration: "none",
  fontSize: 14,
  fontWeight: 500,
};
const taglineStyle: React.CSSProperties = {
  maxWidth: 1200,
  margin: "0 auto",
  padding: "0 20px 12px",
  fontSize: 12,
  color: "var(--muted)",
};
