import { cookies } from "next/headers";
import { NextResponse, type NextRequest } from "next/server";

import { SESSION_COOKIE } from "@/shared/api/cookies";
import { callApi, forwardHeaders, isSameOrigin, jsonError } from "@/shared/api/proxy";

/** Дозволені шляхи Django. Вебхуки, адмінка й службові маршрути через проксі недоступні. */
const RULES: Record<string, RegExp[]> = {
  GET: [
    /^catalog\/products(\/[\w-]+)?$/,
    /^catalog\/search$/,
    /^calc\/config$/,
    /^calc\/estimates\/[A-Za-z0-9]{8}(\/pdf)?$/,
    /^account\/(me|orders|estimates|addresses(\/\d+)?)$/,
    /^delivery\/np\/(cities|warehouses)$/,
    /^orders\/[\w-]{10,}$/,
    /^auth\/methods$/,
  ],
  POST: [
    /^catalog\/prices$/,
    /^calc\/estimates?$/,
    /^leads$/,
    /^account\/addresses$/,
    /^orders\/[\w-]{10,}\/pay$/,
    /^auth\/code\/request$/,
  ],
  PATCH: [/^account\/me$/, /^account\/addresses\/\d+$/],
  DELETE: [/^account\/addresses\/\d+$/],
};
const TRAILING_SLASH = new Set(["leads"]);

async function handle(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const path = (await params).path.join("/");
  const method = req.method.toUpperCase();
  if (!(RULES[method] ?? []).some((rule) => rule.test(path))) {
    return jsonError(403, "forbidden", "Цей запит недоступний");
  }
  if (method !== "GET" && !isSameOrigin(req)) {
    return jsonError(403, "forbidden_origin", "Запит з іншого сайту відхилено");
  }
  const store = await cookies();
  const token = store.get(SESSION_COOKIE)?.value ?? null;
  const hasBody = method === "POST" || method === "PATCH";
  const target = `${path}${TRAILING_SLASH.has(path) ? "/" : ""}${req.nextUrl.search}`;
  const upstream = await callApi(target, {
    method,
    headers: forwardHeaders(req, token, hasBody),
    body: hasBody ? await req.text() : undefined,
  });
  const body = upstream.status === 204 ? null : await upstream.text();
  const response = new NextResponse(body, {
    status: upstream.status,
    headers: { "Content-Type": upstream.headers.get("content-type") ?? "application/json" },
  });
  if (upstream.status === 401 && token) response.cookies.delete(SESSION_COOKIE);
  return response;
}

export { handle as DELETE, handle as GET, handle as PATCH, handle as POST };
