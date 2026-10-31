import "server-only";

import { NextResponse, type NextRequest } from "next/server";

import { apiUrl, clientIpHeaders } from "./server";

/** Заголовки, які сервер Next.js передає в Django від імені браузера. */
export function forwardHeaders(req: NextRequest, token: string | null, withBody: boolean): Record<string, string> {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (withBody) headers["Content-Type"] = "application/json";
  if (token) headers.Authorization = `Bearer ${token}`;
  Object.assign(headers, clientIpHeaders(req.headers));
  const key = req.headers.get("idempotency-key");
  if (key) headers["Idempotency-Key"] = key.slice(0, 64);
  const ua = req.headers.get("user-agent");
  if (ua) headers["User-Agent"] = ua;
  const requestId = req.headers.get("x-request-id");
  if (requestId) headers["X-Request-ID"] = requestId;
  return headers;
}

/** Захист від CSRF для запитів, що змінюють дані: Origin має збігатися з хостом сайту. */
export function isSameOrigin(req: NextRequest): boolean {
  const origin = req.headers.get("origin");
  if (!origin) return false;
  const host = req.headers.get("x-forwarded-host") ?? req.headers.get("host");
  try {
    return new URL(origin).host === host;
  } catch {
    return false;
  }
}

export const jsonError = (status: number, code: string, message: string) =>
  NextResponse.json({ code, message, field: null }, { status });

export async function callApi(path: string, init: { method: string; headers: Record<string, string>; body?: string }) {
  return fetch(apiUrl(path), { ...init, cache: "no-store" });
}

export async function readJson(response: Response): Promise<Record<string, unknown> | null> {
  return response.json().catch(() => null) as Promise<Record<string, unknown> | null>;
}
