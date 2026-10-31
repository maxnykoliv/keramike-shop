import { cookies } from "next/headers";
import { NextResponse, type NextRequest } from "next/server";

import { CART_COOKIE, SESSION_COOKIE } from "@/shared/api/cookies";
import { callApi, forwardHeaders, isSameOrigin, jsonError, readJson } from "@/shared/api/proxy";

/** Оформлення: підставляємо токен кошика з cookie, після успіху кошик закритий і cookie знімається. */
export async function POST(req: NextRequest) {
  if (!isSameOrigin(req)) return jsonError(403, "forbidden_origin", "Запит з іншого сайту відхилено");
  const store = await cookies();
  const cart = store.get(CART_COOKIE)?.value;
  if (!cart) return jsonError(400, "empty_cart", "Кошик порожній");
  const session = store.get(SESSION_COOKIE)?.value ?? null;
  const payload = { ...((await req.json().catch(() => ({}))) as object), cart_token: cart };
  const response = await callApi("orders/", {
    method: "POST", headers: forwardHeaders(req, session, true), body: JSON.stringify(payload),
  });
  const data = await readJson(response);
  const out = NextResponse.json(data, { status: response.status });
  if (response.ok) out.cookies.delete(CART_COOKIE);
  return out;
}
