import "server-only";

import { cookies, headers } from "next/headers";

import { serverEnv } from "@/env";

import { SESSION_COOKIE } from "./cookies";
import { ApiError } from "./errors";

type Options = {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown;
  token?: string | null;
  /** Cache seconds for public data. Without it, no caching. */
  revalidate?: number;
  tags?: string[];
  headers?: Record<string, string>;
};

export const apiUrl = (path: string) => `${serverEnv().API_URL}/api/v1/${path.replace(/^\//, "")}`;

/** A request from the Next.js server to Django. Throws ApiError with the backend error body. */
export async function serverFetch<T>(path: string, options: Options = {}): Promise<T> {
  const { method = "GET", body, token, revalidate, tags, headers: extra } = options;
  const init: RequestInit & { next?: { revalidate?: number; tags?: string[] } } = {
    method,
    headers: {
      Accept: "application/json",
      ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...extra,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  };
  if (revalidate !== undefined && !token && method === "GET") {
    init.next = { revalidate, tags };
  } else {
    init.cache = "no-store";
  }
  const response = await fetch(apiUrl(path), init);
  if (response.status === 204) return undefined as T;
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new ApiError(response.status, data);
  return data as T;
}

/** Public catalog data: cached for 5 minutes, the same for everyone. */
export const publicGet = <T>(path: string, tags: string[] = ["catalog"]) =>
  serverFetch<T>(path, { revalidate: 300, tags });

export async function sessionToken(): Promise<string | null> {
  return (await cookies()).get(SESSION_COOKIE)?.value ?? null;
}

/** Personal data with the current customer's token, uncached. */
export async function accountGet<T>(path: string): Promise<T> {
  return serverFetch<T>(path, { token: await sessionToken() });
}

/**
 * Client IP for backend rate limits. On Vercel the platform itself sets x-forwarded-for,
 * so the first address is the real client. The backend trusts it only together with BFF_SECRET.
 */
export function clientIpHeaders(source: Headers): Record<string, string> {
  const ip = source.get("x-forwarded-for")?.split(",")[0]?.trim() || source.get("x-real-ip");
  const secret = serverEnv().BFF_SECRET;
  return ip && secret ? { "X-Client-IP": ip, "X-BFF-Secret": secret } : {};
}

export async function forwardedFor(): Promise<Record<string, string>> {
  return clientIpHeaders(await headers());
}
