import { NextResponse, type NextRequest } from "next/server";

import { SESSION_COOKIE, SESSION_MAX_AGE, cookieOptions } from "@/shared/api/cookies";
import { callApi, forwardHeaders, isSameOrigin, jsonError, readJson } from "@/shared/api/proxy";

export async function POST(req: NextRequest) {
  if (!isSameOrigin(req)) return jsonError(403, "forbidden_origin", "Запит з іншого сайту відхилено");
  const response = await callApi("auth/code/verify", {
    method: "POST", headers: forwardHeaders(req, null, true), body: await req.text(),
  });
  const data = await readJson(response);
  if (!response.ok || !data) return NextResponse.json(data, { status: response.status });
  const out = NextResponse.json({ customer: data.customer });
  out.cookies.set(SESSION_COOKIE, String(data.token), cookieOptions(SESSION_MAX_AGE));
  return out;
}
