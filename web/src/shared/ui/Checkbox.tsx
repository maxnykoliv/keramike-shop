import type { InputHTMLAttributes, ReactNode } from "react";

import { cn } from "@/shared/lib/cn";

export function Checkbox({ label, hint, className, ...props }: { label: ReactNode; hint?: ReactNode } & InputHTMLAttributes<HTMLInputElement>) {
  return (
    <label className={cn("flex min-h-11 cursor-pointer items-start gap-3 py-2", className)}>
      <input type="checkbox" className="mt-1 size-[18px] shrink-0 cursor-pointer accent-[var(--color-button)]" {...props} />
      <span>
        <span className="block">{label}</span>
        {hint ? <span className="t-small block text-text-muted">{hint}</span> : null}
      </span>
    </label>
  );
}
