import { cn } from "@/shared/lib/cn";
import { formatUah, formatUnitPrice } from "@/shared/lib/money";

/** Ціна: для майстра — його ціна головна, роздрібна поруч приглушено. */
export function Price({
  kop, retailKop, unit, size = "md", className,
}: { kop: number; retailKop?: number | null; unit?: string; size?: "md" | "lg"; className?: string }) {
  const showRetail = retailKop != null && retailKop !== kop;
  const text = unit ? formatUnitPrice(kop, unit) : formatUah(kop);
  return (
    <span className={cn("inline-flex flex-wrap items-baseline gap-x-2", className)}>
      <span className={cn("tabular font-semibold", size === "lg" ? "t-price" : "")} data-testid="price">{text}</span>
      {showRetail ? (
        <span className="t-small text-text-muted tabular" data-testid="retail-price">
          роздріб <s>{unit ? formatUnitPrice(retailKop, unit) : formatUah(retailKop)}</s>
        </span>
      ) : null}
    </span>
  );
}
