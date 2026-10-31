"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback } from "react";

import { request } from "@/shared/api/client";
import type { Customer } from "@/shared/api/types";

export const SESSION_KEY = ["session"] as const;

export function useSession() {
  const query = useQuery({
    queryKey: SESSION_KEY,
    queryFn: () => request<{ customer: Customer | null }>("/api/session"),
    staleTime: 5 * 60_000,
  });
  const customer = query.data?.customer ?? null;
  return { customer, isMaster: Boolean(customer?.is_master), isLoading: query.isLoading };
}

/** After login and logout, reset everything that depends on the customer's status: master prices, cart, calculator. */
export function useRefreshAfterAuth() {
  const client = useQueryClient();
  return useCallback(async () => {
    await Promise.all(["session", "cart", "prices", "calc-config", "addresses"].map((key) =>
      client.invalidateQueries({ queryKey: [key] })));
  }, [client]);
}
