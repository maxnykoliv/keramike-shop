"use client";

import { Icon } from "@/shared/ui";

/** − number +: quantity in whole packs only. */
export function QtyStepper({
  value, onChange, min = 1, max = 9999, label, disabled,
}: { value: number; onChange: (value: number) => void; min?: number; max?: number; label: string; disabled?: boolean }) {
  const set = (v: number) => onChange(Math.min(max, Math.max(min, Math.round(v) || min)));
  return (
    <div className="inline-flex items-center border border-line-strong" role="group" aria-label={label}>
      <button type="button" className="grid size-11 place-items-center disabled:opacity-40" aria-label="Менше"
        onClick={() => set(value - 1)} disabled={disabled || value <= min}><Icon name="minus" size={16} /></button>
      <input aria-label={label} inputMode="numeric" value={value} disabled={disabled}
        onChange={(e) => set(Number(e.target.value.replace(/\D/g, "")))}
        className="tabular h-11 w-12 bg-transparent text-center focus:outline-none" />
      <button type="button" className="grid size-11 place-items-center disabled:opacity-40" aria-label="Більше"
        onClick={() => set(value + 1)} disabled={disabled || value >= max}><Icon name="plus" size={16} /></button>
    </div>
  );
}
