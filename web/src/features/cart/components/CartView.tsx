"use client";

import Link from "next/link";

import type { CartLine } from "@/shared/api/types";
import { track } from "@/shared/lib/analytics";
import { formatUah } from "@/shared/lib/money";
import { formatDecimal, unitLabel } from "@/shared/lib/numbers";
import { ButtonLink, Icon, Notice, Skeleton } from "@/shared/ui";

import { useCart, useCartActions } from "../hooks/useCart";
import { QtyStepper } from "./QtyStepper";

function groupLines(lines: CartLine[]) {
  const groups = new Map<string, CartLine[]>();
  for (const line of lines) {
    const key = line.group_label || "";
    groups.set(key, [...(groups.get(key) ?? []), line]);
  }
  return [...groups.entries()];
}

export function CartView() {
  const { data: cart, isLoading } = useCart();
  const { update, remove } = useCartActions();

  if (isLoading) return <div className="flex flex-col gap-4"><Skeleton className="h-24" /><Skeleton className="h-24" /></div>;
  if (!cart || cart.lines.length === 0) {
    return (
      <div className="flex flex-col items-start gap-6 py-10" data-testid="cart-empty">
        <p className="t-h2">Кошик порожній</p>
        <p className="text-text-muted">Порахуйте ремонт у калькуляторі або оберіть плитку в каталозі.</p>
        <div className="flex flex-wrap gap-3">
          <ButtonLink href="/calculator">Порахувати ремонт</ButtonLink>
          <ButtonLink href="/catalog" variant="secondary">Каталог</ButtonLink>
        </div>
      </div>
    );
  }

  const weight = Number(cart.weight_kg);
  return (
    <div className="grid gap-10 md:grid-cols-[1fr_360px] md:items-start">
      <div className="flex flex-col gap-10">
        {groupLines(cart.lines).map(([group, lines]) => (
          <section key={group || "items"} aria-label={group || "Товари"}>
            {group ? <h2 className="t-label mb-4 text-text-muted">{group}</h2> : null}
            <ul className="divide-y divide-line border-y border-line">
              {lines.map((line) => (
                <li key={line.id} data-testid="cart-line" className="grid grid-cols-[1fr_auto] gap-x-4 gap-y-3 py-5">
                  <div>
                    <p className="font-medium">{line.name}</p>
                    <p className="t-small text-text-muted">
                      Артикул {line.sku}
                      {line.unit === "pack" ? ` · ${formatDecimal(line.base_qty)} м²` : ""}
                    </p>
                    {!line.available ? <Notice className="mt-2">Немає потрібної кількості на складі, менеджер уточнить терміни.</Notice> : null}
                  </div>
                  <p className="tabular text-right font-semibold" data-testid="line-total">{line.total_display}</p>
                  <div className="flex items-center gap-3">
                    <QtyStepper label={`Кількість, ${unitLabel(line.unit)}`} value={line.qty}
                      onChange={(qty) => update.mutate({ id: line.id, qty })} />
                    <span className="t-small text-text-muted">{unitLabel(line.unit)}</span>
                  </div>
                  <button type="button" onClick={() => remove.mutate(line.id)}
                    className="t-small inline-flex items-center gap-1 justify-self-end text-text-muted hover:text-text"
                    aria-label={`Видалити ${line.name}`}>
                    <Icon name="trash" size={16} /> Видалити
                  </button>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>
      <aside className="sticky bottom-0 flex flex-col gap-4 border-t border-line bg-bg py-5 md:top-28 md:border md:p-6" aria-label="Підсумок">
        {cart.has_unavailable ? <Notice>Частини товарів бракує на складі.</Notice> : null}
        <dl className="flex flex-col gap-2">
          <div className="flex justify-between"><dt className="text-text-muted">Вага</dt><dd className="tabular">{formatDecimal(weight.toFixed(1))} кг</dd></div>
          <div className="flex items-baseline justify-between"><dt>Разом</dt><dd className="t-price" data-testid="cart-total">{formatUah(cart.subtotal_kop)}</dd></div>
        </dl>
        <p className="t-small text-text-muted">Вартість доставки — на наступному кроці.</p>
        <ButtonLink href="/checkout" fullWidth onClick={() => track("begin_checkout", { value: cart.subtotal_kop / 100 })}>
          Оформити замовлення
        </ButtonLink>
        <Link href="/catalog" className="link t-small text-center">Продовжити покупки</Link>
      </aside>
    </div>
  );
}
