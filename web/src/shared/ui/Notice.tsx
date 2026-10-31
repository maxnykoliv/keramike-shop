import type { ReactNode } from "react";

import { cn } from "@/shared/lib/cn";

type Tone = "warning" | "info" | "error" | "success";
const tones: Record<Tone, string> = {
  warning: "border-accent",
  info: "border-line-strong",
  error: "border-error text-error",
  success: "border-success",
};

/** Попередження: тонка лінія зліва, текст Small. */
export function Notice({ tone = "warning", children, className }: { tone?: Tone; children: ReactNode; className?: string }) {
  return (
    <div role={tone === "error" ? "alert" : "status"} className={cn("t-small border-l-2 py-1 pl-3", tones[tone], className)}>
      {children}
    </div>
  );
}
