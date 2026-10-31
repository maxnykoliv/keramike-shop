"use client";

import { useCallback } from "react";
import { useQuery } from "@tanstack/react-query";

import { useSession } from "@/features/auth";
import { bff } from "@/shared/api/client";
import type { PricesResponse } from "@/shared/api/types";

import type { CalcForm } from "../model";

/** Master prices for the form's tiles, so the instant calculation matches the server. */
export function usePersonalPricesForTiles(form: CalcForm | null) {
  const { isMaster } = useSession();
  const ids = [...new Set((form?.surfaces ?? []).flatMap((s) => (s.tile?.source === "catalog" ? [s.tile.productId] : [])))].sort();
  const query = useQuery({
    queryKey: ["prices", ids],
    queryFn: () => bff<PricesResponse>("catalog/prices", { method: "POST", body: { ids } }),
    enabled: isMaster && ids.length > 0,
    staleTime: 5 * 60_000,
  });
  const prices = query.data?.prices;
  const priceOf = useCallback(
    (id: number, fallback: number) => (isMaster ? prices?.[String(id)] ?? fallback : fallback),
    [isMaster, prices],
  );
  return { priceOf, loading: isMaster && query.isLoading };
}
