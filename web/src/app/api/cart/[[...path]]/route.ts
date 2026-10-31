import { cookies } from "next/headers";
import { NextResponse, type NextRequest } from "next/server";

import { CART_COOKIE, CART_MAX_AGE, SESSION_COOKIE, cookieOptions } from "@/shared/api/cookies";
import { callApi, forwardHeaders, isSameOrigin, jsonError, readJson } from "@/shared/api/proxy";

/** Кошик через сервер Next.js: токен кошика живе в httpOnly cookie, браузер його не бачить. */
const EMPTY_CART = {
  token: "",
  lines: [],
  subtotal_kop: 0,
  subtotal_display: "0,00 грн",
  weight_kg: "0.000",
  has_unavailable: false,
};

type Ctx = { params: Promise<{ path?: string[] }> };

function hideToken(data: Record<string, unknown> | null) {
  return data && "token" in data ? { ...data, token: "" } : data;
}

async function createCart(req: NextRequest, session: string | null): Promise<string | null> {
  const response = await callApi("carts/", { method: "POST", headers: forwardHeaders(req, session, false) });
  const data = await readJson(response);
  return response.ok && typeof data?.token === "string" ? data.token : null;
}

async function handle(req: NextRequest, { params }: Ctx) {
  const path = (await params).path ?? [];
  const method = req.method.toUpperCase();
  if (method !== "GET" && !isSameOrigin(req)) return jsonError(403, "forbidden_origin", "Запит з іншого сайту відхилено");

  const store = await cookies();
  const session = store.get(SESSION_COOKIE)?.value ?? null;
  let token = store.get(CART_COOKIE)?.value ?? null;
  const [action, arg] = path;

  // GET /api/cart — вміст кошика. Без кошика — порожній, нічого не створюємо.
  if (method === "GET" && !action) {
    if (!token) return NextResponse.json(EMPTY_CART);
    const response = await callApi(`carts/${token}`, { method: "GET", headers: forwardHeaders(req, session, false) });
    if (response.status === 404) {
      const out = NextResponse.json(EMPTY_CART);
      out.cookies.delete(CART_COOKIE);
      return out;
    }
    return NextResponse.json(hideToken(await readJson(response)), { status: response.status });
  }

  const body = method === "POST" || method === "PATCH" ? await req.text() : undefined;

  if (action === "quote" && method === "POST") {
    if (!token) return jsonError(400, "empty_cart", "Кошик порожній");
    const payload = { ...(JSON.parse(body || "{}") as object), cart_token: token };
    const response = await callApi("delivery/quote", {
      method: "POST", headers: forwardHeaders(req, session, true), body: JSON.stringify(payload),
    });
    const data = await readJson(response);
    if (data && "cart_token" in data) delete data.cart_token;
    return NextResponse.json(data, { status: response.status });
  }

  let upstreamPath: string;
  if (action === "items" && method === "POST" && !arg) upstreamPath = "items";
  else if (action === "items" && arg && /^\d+$/.test(arg) && (method === "PATCH" || method === "DELETE")) upstreamPath = `items/${arg}`;
  else if (action === "from-estimate" && arg && /^[A-Za-z0-9]{8}$/.test(arg) && method === "POST") upstreamPath = `from-estimate/${arg}`;
  else return jsonError(404, "not_found", "Не знайдено");

  // Додавання створює кошик за потреби; протермінований кошик замінюється новим.
  const creates = method === "POST";
  let created = false;
  if (!token && creates) {
    token = await createCart(req, session);
    created = true;
  }
  if (!token) return jsonError(404, "not_found", "Кошик не знайдено");

  const call = (cartToken: string) => callApi(`carts/${cartToken}/${upstreamPath}`, {
    method, headers: forwardHeaders(req, session, body !== undefined), body,
  });
  let response = await call(token);
  if (response.status === 404 && creates && !created) {
    const fresh = await createCart(req, session);
    if (fresh) {
      token = fresh;
      created = true;
      response = await call(token);
    }
  }
  const out = NextResponse.json(hideToken(await readJson(response)), { status: response.status });
  if (created && response.ok) out.cookies.set(CART_COOKIE, token, cookieOptions(CART_MAX_AGE));
  return out;
}

export { handle as DELETE, handle as GET, handle as PATCH, handle as POST };
