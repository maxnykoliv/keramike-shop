import { cookies } from "next/headers";
import { NextResponse, type NextRequest } from "next/server";

import { SESSION_COOKIE } from "@/shared/api/cookies";
import { callApi, forwardHeaders, isSameOrigin, jsonError } from "@/shared/api/proxy";

/** Вихід: {all: true} завершує сесії на всіх пристроях. */
export async function POST(req: NextRequest) {
  if (!isSameOrigin(req)) return jsonError(403, "forbidden_origin", "Запит з іншого сайту відхилено");
  const token = (await cookies()).get(SESSION_COOKIE)?.value ?? null;
  const { all } = (await req.json().catch(() => ({}))) as { all?: boolean };
  if (token) {
    await callApi(all ? "auth/logout-all" : "auth/logout", {
      method: "POST", headers: forwardHeaders(req, token, false),
    }).catch(() => null);
  }
  const out = new NextResponse(null, { status: 204 });
  out.cookies.delete(SESSION_COOKIE);
  return out;
}
