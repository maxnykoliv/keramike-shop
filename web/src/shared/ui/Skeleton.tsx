import { cn } from "@/shared/lib/cn";

export function Skeleton({ className }: { className?: string }) {
  return <div aria-hidden="true" className={cn("rounded-[2px] bg-surface animate-[pulse-soft_1.6s_ease-in-out_infinite]", className)} />;
}
