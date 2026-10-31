"use client";

import { useQuery } from "@tanstack/react-query";

import type { CalcSettings } from "@/calc";
import { bff } from "@/shared/api/client";

/** Активні налаштування калькулятора. Для майстра бекенд одразу підставляє його ціни матеріалів. */
export function useCalcConfig() {
  return useQuery({
    queryKey: ["calc-config"],
    queryFn: () => bff<CalcSettings>("calc/config"),
    staleTime: 10 * 60_000,
  });
}
