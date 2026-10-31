/** Browser requests. They only go to the site's own domain: /api/bff, /api/cart, /api/auth. */
import { ApiError } from "./errors";

type Init = { method?: "GET" | "POST" | "PATCH" | "DELETE"; body?: unknown; headers?: Record<string, string> };

export async function request<T>(url: string, { method = "GET", body, headers }: Init = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(url, {
      method,
      headers: {
        Accept: "application/json",
        ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
        ...headers,
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
      credentials: "same-origin",
    });
  } catch {
    throw new ApiError(0, { code: "network", message: "Немає з'єднання. Перевірте інтернет і спробуйте ще раз." });
  }
  if (response.status === 204) return undefined as T;
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new ApiError(response.status, data);
  return data as T;
}

/** Proxy to Django through the Next.js server: path without /api/v1, e.g. "calc/config". */
export const bff = <T>(path: string, init?: Init) => request<T>(`/api/bff/${path.replace(/^\//, "")}`, init);
