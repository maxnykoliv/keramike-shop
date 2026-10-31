import type { ReactNode } from "react";

import { cn } from "@/shared/lib/cn";

export function Badge({ children, tone = "neutral" }: { children: ReactNode; tone?: "neutral" | "accent" | "success" }) {
  return (
    <span className={cn("t-label inline-flex items-center rounded-[2px] border px-2 py-0.5",
      tone === "accent" && "border-accent text-accent-strong",
      tone === "success" && "border-success text-success",
      tone === "neutral" && "border-line text-text-muted")}>
      {children}
    </span>
  );
}
