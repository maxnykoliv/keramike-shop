"use client";

import { useQuery } from "@tanstack/react-query";

import { useSession } from "@/features/auth";
import { bff } from "@/shared/api/client";
import type { PricesResponse } from "@/shared/api/types";

/**
 * Ціни майстра поверх кешованого каталогу. Для звичайних клієнтів запит не робиться:
 * каталог уже показує роздрібні ціни.
 */
export function usePersonalPrices(ids: number[]) {
  const { isMaster } = useSession();
  const unique = [...new Set(ids)].sort((a, b) => a - b);
  const query = useQuery({
    queryKey: ["prices", unique],
    queryFn: () => bff<PricesResponse>("catalog/prices", { method: "POST", body: { ids: unique } }),
    enabled: isMaster && unique.length > 0,
    staleTime: 5 * 60_000,
  });
  const prices = isMaster ? query.data?.prices ?? {} : {};
  return { isMaster, priceOf: (id: number, fallback: number) => prices[String(id)] ?? fallback };
}
