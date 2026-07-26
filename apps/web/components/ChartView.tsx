"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ChartSpec } from "@/lib/api";

export function ChartView({ spec }: { spec: ChartSpec }) {
  if (spec.type === "metric") {
    const formatted =
      typeof spec.value === "number"
        ? spec.value.toLocaleString(undefined, { maximumFractionDigits: 2 })
        : String(spec.value ?? "—");
    return (
      <div style={metricStyle}>
        <div style={{ color: "var(--muted)", fontSize: 14 }}>{spec.label}</div>
        <div style={{ fontSize: 36, fontWeight: 700 }}>{formatted}</div>
      </div>
    );
  }

  if (spec.type === "line") {
    return (
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={spec.data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey={spec.x} tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip />
          <Line type="monotone" dataKey={spec.y} stroke="#2563eb" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    );
  }

  if (spec.type === "bar") {
    return (
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={spec.data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey={spec.x} tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip />
          <Bar dataKey={spec.y} fill="#2563eb" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    );
  }

  return (
    <div style={{ overflowX: "auto" }}>
      <table style={tableStyle}>
        <thead>
          <tr>
            {spec.columns.map((c) => (
              <th key={c} style={thStyle}>
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {spec.data.map((row, i) => (
            <tr key={i}>
              {spec.columns.map((c) => (
                <td key={c} style={tdStyle}>
                  {String(row[c] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const metricStyle: React.CSSProperties = {
  padding: "24px",
  background: "linear-gradient(135deg, #eff6ff 0%, #f8fafc 100%)",
  borderRadius: 12,
  border: "1px solid var(--border)",
};

const tableStyle: React.CSSProperties = {
  width: "100%",
  borderCollapse: "collapse",
  fontSize: 13,
};

const thStyle: React.CSSProperties = {
  textAlign: "left",
  padding: "8px 12px",
  borderBottom: "2px solid var(--border)",
  background: "#f1f5f9",
};

const tdStyle: React.CSSProperties = {
  padding: "8px 12px",
  borderBottom: "1px solid var(--border)",
};
