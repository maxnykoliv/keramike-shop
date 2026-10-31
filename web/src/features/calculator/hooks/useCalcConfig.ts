"use client";

import { useQuery } from "@tanstack/react-query";

import type { CalcSettings } from "@/calc";
import { bff } from "@/shared/api/client";

/** Active calculator settings. For a master, the backend already includes their material prices. */
export function useCalcConfig() {
  return useQuery({
    queryKey: ["calc-config"],
    queryFn: () => bff<CalcSettings>("calc/config"),
    staleTime: 10 * 60_000,
  });
}
