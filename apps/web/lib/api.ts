const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY ?? "";

export type ChartSpec =
  | { type: "metric"; label: string; value: unknown }
  | { type: "line"; x: string; y: string; data: Record<string, unknown>[] }
  | { type: "bar"; x: string; y: string; data: Record<string, unknown>[] }
  | { type: "table"; columns: string[]; data: Record<string, unknown>[] };

export type Insight = {
  headline: string;
  bullets: string[];
  caveats: string[];
  follow_ups: string[];
};

export type AgentTraceStep = {
  agent: string;
  action: string;
  detail: string;
  duration_ms: number;
};

export type AssistantMessage = {
  text: string;
  insight: Insight;
  sql: string;
  status: string;
  row_count: number;
  duration_ms: number;
  columns: string[];
  result_preview: Record<string, unknown>[];
  chart_spec: ChartSpec | null;
  error?: string;
  sql_source?: string;
  query_run_id?: string;
  agent_trace?: AgentTraceStep[];
  intent?: string;
  mode?: string;
  plan_steps?: string[];
  investigation_runs?: { purpose: string; sql: string; row_count: number }[];
  driver_rankings?: { rank: number; driver: string; metric: string; value: unknown; source?: string }[];
  resolved_question?: string;
};

export type QueryRunAudit = {
  id: string;
  question_text: string | null;
  sql_text: string;
  status: string;
  row_count: number | null;
  duration_ms: number | null;
  error_message: string | null;
  created_at: string;
  feedback_rating: number | null;
};

function apiHeaders(): HeadersInit {
  const h: Record<string, string> = { "Content-Type": "application/json" };
  if (API_KEY) h["X-API-Key"] = API_KEY;
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("insightbridge_token");
    if (token) h["Authorization"] = `Bearer ${token}`;
  }
  return h;
}

export async function requestMagicLink(email: string) {
  const res = await fetch(`${API_URL}/v1/auth/magic-link`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<{ magic_link_token?: string; email: string }>;
}

export async function verifyMagicLink(token: string) {
  const res = await fetch(`${API_URL}/v1/auth/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<{ access_token: string }>;
}

export async function fetchMe() {
  const res = await fetch(`${API_URL}/v1/me`, { headers: apiHeaders() });
  if (!res.ok) return null;
  return res.json();
}

export async function createConversation(title?: string) {
  const res = await fetch(`${API_URL}/v1/conversations`, {
    method: "POST",
    headers: apiHeaders(),
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<{ id: string; title: string | null; created_at: string }>;
}

export async function askQuestion(conversationId: string, question: string) {
  const res = await fetch(`${API_URL}/v1/conversations/${conversationId}/ask`, {
    method: "POST",
    headers: apiHeaders(),
    body: JSON.stringify({ question }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<{
    assistant_message: { id: string; content: AssistantMessage };
    query_run_id: string;
  }>;
}

export async function fetchHealth() {
  const res = await fetch(`${API_URL}/health`, { cache: "no-store" });
  if (!res.ok) return null;
  return res.json() as Promise<{ status: string; demo_mode: boolean; api_key_required?: boolean }>;
}

export async function fetchAuditLog(limit = 50) {
  const res = await fetch(`${API_URL}/v1/audit/query-runs?limit=${limit}`, { cache: "no-store" });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<{ items: QueryRunAudit[] }>;
}

export async function submitFeedback(queryRunId: string, rating: -1 | 1) {
  const res = await fetch(`${API_URL}/v1/query-runs/${queryRunId}/feedback`, {
    method: "POST",
    headers: apiHeaders(),
    body: JSON.stringify({ rating }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function fetchAgentCapabilities() {
  const res = await fetch(`${API_URL}/v1/agent/capabilities`, { cache: "no-store" });
  if (!res.ok) return null;
  return res.json();
}

export { API_URL, apiHeaders };
