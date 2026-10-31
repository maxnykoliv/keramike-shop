import { cookies } from "next/headers";
import { NextResponse, type NextRequest } from "next/server";

import { LOGIN_COOKIE, SESSION_COOKIE, SESSION_MAX_AGE, cookieOptions } from "@/shared/api/cookies";
import { callApi, forwardHeaders, isSameOrigin, jsonError, readJson } from "@/shared/api/proxy";

export async function POST(req: NextRequest) {
  if (!isSameOrigin(req)) return jsonError(403, "forbidden_origin", "Запит з іншого сайту відхилено");
  const raw = (await cookies()).get(LOGIN_COOKIE)?.value;
  if (!raw) return NextResponse.json({ status: "expired" });
  let attempt: { login_id: string; poll_secret: string };
  try {
    attempt = JSON.parse(raw);
  } catch {
    return NextResponse.json({ status: "expired" });
  }
  const response = await callApi("auth/telegram/poll", {
    method: "POST", headers: forwardHeaders(req, null, true), body: JSON.stringify(attempt),
  });
  const data = await readJson(response);
  if (response.status === 404 || data?.status === "expired") {
    const out = NextResponse.json({ status: "expired" });
    out.cookies.delete(LOGIN_COOKIE);
    return out;
  }
  if (!response.ok) return NextResponse.json(data, { status: response.status });
  if (data?.status !== "confirmed") return NextResponse.json({ status: data?.status ?? "pending" });

  const out = NextResponse.json({ status: "confirmed", customer: data.customer });
  out.cookies.set(SESSION_COOKIE, String(data.token), cookieOptions(SESSION_MAX_AGE));
  out.cookies.delete(LOGIN_COOKIE);
  return out;
}
