import { cookies } from "next/headers";
import { NextResponse, type NextRequest } from "next/server";

import { SESSION_COOKIE } from "@/shared/api/cookies";
import { callApi, forwardHeaders, readJson } from "@/shared/api/proxy";

/** Профіль поточного клієнта для інтерфейсу. Токен у відповідь не потрапляє. */
export async function GET(req: NextRequest) {
  const token = (await cookies()).get(SESSION_COOKIE)?.value;
  if (!token) return NextResponse.json({ customer: null });
  const response = await callApi("account/me", { method: "GET", headers: forwardHeaders(req, token, false) });
  if (response.status === 401) {
    const out = NextResponse.json({ customer: null });
    out.cookies.delete(SESSION_COOKIE);
    return out;
  }
  if (!response.ok) return NextResponse.json({ customer: null, error: true }, { status: 200 });
  return NextResponse.json({ customer: await readJson(response) }, {
    headers: { "Cache-Control": "private, no-store" },
  });
}
