import type { ReactNode } from "react";

import { cn } from "@/shared/lib/cn";

export type RadioOption<T extends string> = { value: T; label: ReactNode; description?: ReactNode; icon?: ReactNode };

/** Options as cards: thin border, graphite border when selected. */
export function RadioCards<T extends string>({
  legend, name, value, onChange, options, columns = 2, error,
}: {
  legend: ReactNode;
  name: string;
  value: T | null;
  onChange: (value: T) => void;
  options: RadioOption<T>[];
  columns?: 2 | 3 | 4;
  error?: string | null;
}) {
  const grid = { 2: "grid-cols-2", 3: "grid-cols-2 md:grid-cols-3", 4: "grid-cols-2 md:grid-cols-4" }[columns];
  return (
    <fieldset className="flex flex-col gap-3">
      <legend className="t-small mb-3 font-medium">{legend}</legend>
      <div className={cn("grid gap-3", grid)}>
        {options.map((option) => {
          const checked = option.value === value;
          return (
            <label key={option.value}
              className={cn(
                "relative flex min-h-14 cursor-pointer flex-col justify-center gap-1 rounded-[2px] border px-4 py-3 transition-colors",
                "has-[:focus-visible]:outline has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-2",
                checked ? "border-text bg-surface/40" : "border-line hover:border-line-strong",
              )}>
              <input type="radio" name={name} value={option.value} checked={checked}
                onChange={() => onChange(option.value)} className="sr-only" />
              <span className="flex items-center gap-2 font-medium">{option.icon}{option.label}</span>
              {option.description ? <span className="t-small text-text-muted">{option.description}</span> : null}
            </label>
          );
        })}
      </div>
      {error ? <p role="alert" className="t-small text-error">{error}</p> : null}
    </fieldset>
  );
}
