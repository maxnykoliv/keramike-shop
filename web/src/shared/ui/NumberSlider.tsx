"use client";

import { useId } from "react";

import { cn } from "@/shared/lib/cn";
import { formatDecimal, parseDecimal } from "@/shared/lib/numbers";

/**
 * A number with a slider, as in the client's earlier "Калькулятор MAX": the slider for rough values, the field for exact ones.
 * The value is a dot-decimal string ("2.5"); a comma typed by the user is converted.
 */
export function NumberSlider({
  label, value, onChange, min, max, step = 0.05, unit, error, name,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  min: number;
  max: number;
  step?: number;
  unit?: string;
  error?: string | null;
  name?: string;
}) {
  const id = `n${useId()}`;
  const errorId = error ? `${id}-error` : undefined;
  const numeric = Number(parseDecimal(value) ?? min);
  const clamped = Math.min(max, Math.max(min, Number.isFinite(numeric) ? numeric : min));
  return (
    <div className="flex flex-col gap-2">
      <label htmlFor={id} className="t-small font-medium">{label}</label>
      <div className="flex items-center gap-4">
        <input type="range" min={min} max={max} step={step} value={clamped}
          aria-label={`${label}: повзунок`} tabIndex={-1}
          onChange={(e) => onChange(String(Number(e.target.value)))}
          className="h-1 flex-1 cursor-pointer appearance-none rounded-full bg-line accent-[var(--color-accent)]" />
        <div className={cn("flex w-28 items-baseline gap-1 border-b border-line-strong", error && "border-error")}>
          <input id={id} name={name} inputMode="decimal" autoComplete="off" value={formatDecimal(value)}
            aria-invalid={Boolean(error) || undefined} aria-describedby={errorId}
            onChange={(e) => onChange(e.target.value.replace(",", "."))}
            className="tabular w-full min-h-11 bg-transparent px-1 text-right focus:outline-none" />
          {unit ? <span className="t-small text-text-muted" aria-hidden="true">{unit}</span> : null}
        </div>
      </div>
      {error ? <p id={errorId} role="alert" className="t-small text-error">{error}</p> : null}
    </div>
  );
}
