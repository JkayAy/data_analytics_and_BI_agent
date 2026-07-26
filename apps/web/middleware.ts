import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

const COOKIE = "insightbridge_demo";
const password = process.env.DEMO_ACCESS_PASSWORD;

export function middleware(request: NextRequest) {
  if (!password) return NextResponse.next();

  const { pathname } = request.nextUrl;
  if (
    pathname.startsWith("/gate") ||
    pathname.startsWith("/api") ||
    pathname.startsWith("/_next") ||
    pathname === "/favicon.ico"
  ) {
    return NextResponse.next();
  }

  if (request.cookies.get(COOKIE)?.value === "1") {
    return NextResponse.next();
  }

  const url = request.nextUrl.clone();
  url.pathname = "/gate";
  url.searchParams.set("from", pathname);
  return NextResponse.redirect(url);
}

export const config = {
  matcher: ["/((?!_next/static|_next/image).*)"],
};
