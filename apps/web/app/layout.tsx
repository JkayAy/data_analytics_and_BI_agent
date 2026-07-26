import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "InsightBridge — Conversational BI",
  description:
    "Natural language to validated SQL, insights, and charts. Portfolio demo for data bottleneck problems.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
