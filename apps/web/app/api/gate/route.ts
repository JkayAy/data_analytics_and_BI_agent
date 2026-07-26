import { NextResponse } from "next/server";

export async function POST(request: Request) {
  const expected = process.env.DEMO_ACCESS_PASSWORD;
  if (!expected) {
    return NextResponse.json({ ok: true });
  }
  const body = (await request.json()) as { password?: string };
  if (body.password !== expected) {
    return NextResponse.json({ ok: false }, { status: 401 });
  }
  const res = NextResponse.json({ ok: true });
  res.cookies.set("insightbridge_demo", "1", {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    maxAge: 60 * 60 * 24 * 7,
    path: "/",
  });
  return res;
}
