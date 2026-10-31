import { NextResponse, type NextRequest } from "next/server";

import { LOGIN_COOKIE, LOGIN_MAX_AGE, cookieOptions } from "@/shared/api/cookies";
import { callApi, forwardHeaders, isSameOrigin, jsonError, readJson } from "@/shared/api/proxy";

/** Login start: the polling secret stays in an httpOnly cookie; the browser only gets the bot link. */
export async function POST(req: NextRequest) {
  if (!isSameOrigin(req)) return jsonError(403, "forbidden_origin", "Запит з іншого сайту відхилено");
  const response = await callApi("auth/telegram/start", { method: "POST", headers: forwardHeaders(req, null, false) });
  const data = await readJson(response);
  if (!response.ok || !data) return NextResponse.json(data, { status: response.status });
  const out = NextResponse.json({ bot_url: data.bot_url, expires_at: data.expires_at });
  out.cookies.set(LOGIN_COOKIE, JSON.stringify({ login_id: data.login_id, poll_secret: data.poll_secret }),
    cookieOptions(LOGIN_MAX_AGE));
  return out;
}
