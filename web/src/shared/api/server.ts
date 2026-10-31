import "server-only";

import { cookies, headers } from "next/headers";

import { serverEnv } from "@/env";

import { SESSION_COOKIE } from "./cookies";
import { ApiError } from "./errors";

type Options = {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown;
  token?: string | null;
  /** Секунди кешу для публічних даних. Без нього — без кешу. */
  revalidate?: number;
  tags?: string[];
  headers?: Record<string, string>;
};

export const apiUrl = (path: string) => `${serverEnv().API_URL}/api/v1/${path.replace(/^\//, "")}`;

/** Запит із сервера Next.js до Django. Кидає ApiError з тілом помилки бекенду. */
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

/** Публічні дані каталогу: кеш 5 хвилин, однаковий для всіх. */
export const publicGet = <T>(path: string, tags: string[] = ["catalog"]) =>
  serverFetch<T>(path, { revalidate: 300, tags });

export async function sessionToken(): Promise<string | null> {
  return (await cookies()).get(SESSION_COOKIE)?.value ?? null;
}

/** Особисті дані з токеном поточного клієнта, без кешу. */
export async function accountGet<T>(path: string): Promise<T> {
  return serverFetch<T>(path, { token: await sessionToken() });
}

/**
 * IP клієнта для лімітів бекенду. На Vercel x-forwarded-for виставляє сама платформа,
 * тож перша адреса — справжній клієнт. Бекенд вірить їй лише разом із BFF_SECRET.
 */
export function clientIpHeaders(source: Headers): Record<string, string> {
  const ip = source.get("x-forwarded-for")?.split(",")[0]?.trim() || source.get("x-real-ip");
  const secret = serverEnv().BFF_SECRET;
  return ip && secret ? { "X-Client-IP": ip, "X-BFF-Secret": secret } : {};
}

export async function forwardedFor(): Promise<Record<string, string>> {
  return clientIpHeaders(await headers());
}
