"use client";

import { useMemo } from "react";

import { CalcValidationError, calculate, type CalcResult, type CalcSettings } from "@/calc";

import { toEngineInput, type CalcForm } from "../model";

export type Calculation =
  | { state: "ready"; result: CalcResult }
  | { state: "invalid"; field: string; message: string }
  | { state: "loading" };

/** Instant in-browser calculation with the same engine as the server (checked by calc-cases). */
export function useCalculation(form: CalcForm, settings: CalcSettings | undefined,
  priceOf?: (id: number, fallback: number) => number): Calculation {
  return useMemo(() => {
    if (!settings) return { state: "loading" };
    const built = toEngineInput(form, priceOf);
    if ("error" in built) return { state: "invalid", ...built.error };
    try {
      return { state: "ready", result: calculate(built.input, settings) };
    } catch (e) {
      if (e instanceof CalcValidationError) return { state: "invalid", field: e.field, message: e.message };
      throw e;
    }
  }, [form, settings, priceOf]);
}
