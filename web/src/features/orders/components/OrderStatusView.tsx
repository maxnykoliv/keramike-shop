import type { PublicOrder } from "@/shared/api/types";
import { cn } from "@/shared/lib/cn";
import { formatUah } from "@/shared/lib/money";
import { formatDecimal, unitLabel } from "@/shared/lib/numbers";
import { Badge } from "@/shared/ui";

import { DELIVERY_LABELS, ORDER_STEPS, PAYMENT_LABELS } from "../labels";

/** Order status page: steps, payment, lines, totals. */
export function OrderStatusView({ order }: { order: PublicOrder }) {
  const cancelled = order.status === "cancelled";
  const currentIndex = ORDER_STEPS.findIndex((s) => s.status === order.status);
  return (
    <div className="flex flex-col gap-10">
      <div className="flex flex-wrap items-center gap-3">
        <Badge tone={cancelled ? "neutral" : "accent"}><span data-testid="order-status">{order.status_label}</span></Badge>
        <Badge tone={order.payment_status === "paid" ? "success" : "neutral"}>
          <span data-testid="payment-status">{order.payment_status_label}</span>
        </Badge>
      </div>
      {!cancelled ? (
        <ol className="grid grid-cols-5 gap-2" aria-label="Етапи замовлення">
          {ORDER_STEPS.map((step, i) => (
            <li key={step.status} aria-current={i === currentIndex ? "step" : undefined}
              className={cn("t-small border-t-2 pt-2", i <= currentIndex ? "border-accent text-text" : "border-line text-text-muted")}>
              {step.label}
            </li>
          ))}
        </ol>
      ) : null}
      <section aria-labelledby="items-title">
        <h2 id="items-title" className="t-h3 mb-4">Позиції</h2>
        <ul className="divide-y divide-line border-y border-line">
          {order.items.map((item, i) => (
            <li key={`${item.sku}-${i}`} className="flex justify-between gap-4 py-4">
              <div>
                <p>{item.name}</p>
                <p className="t-small text-text-muted tabular">
                  {item.qty} {unitLabel(item.unit)}{item.unit === "pack" ? ` · ${formatDecimal(item.qty_base)} м²` : ""}
                </p>
              </div>
              <p className="tabular shrink-0">{formatUah(item.total_kop)}</p>
            </li>
          ))}
        </ul>
      </section>
      <dl className="grid max-w-md gap-2">
        <div className="flex justify-between"><dt className="text-text-muted">Доставка</dt><dd>{DELIVERY_LABELS[order.delivery_method]}</dd></div>
        <div className="flex justify-between"><dt className="text-text-muted">Оплата</dt><dd>{PAYMENT_LABELS[order.payment_method]}</dd></div>
        <div className="flex justify-between"><dt className="text-text-muted">Товари</dt><dd className="tabular">{formatUah(order.subtotal_kop)}</dd></div>
        <div className="flex justify-between"><dt className="text-text-muted">Вартість доставки</dt>
          <dd className="tabular">{order.delivery_kop == null ? "уточнить менеджер" : formatUah(order.delivery_kop)}</dd></div>
        <div className="flex items-baseline justify-between border-t border-line pt-3"><dt className="font-semibold">Разом</dt>
          <dd className="t-price" data-testid="order-total">{formatUah(order.total_kop)}</dd></div>
      </dl>
    </div>
  );
}
