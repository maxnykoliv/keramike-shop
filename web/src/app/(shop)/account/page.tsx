import Link from "next/link";
import { connection } from "next/server";

import { accountData } from "@/features/account/server";
import type { Customer, PaginatedEstimates, PaginatedOrders } from "@/shared/api/types";
import { formatUah } from "@/shared/lib/money";
import { formatPhone } from "@/shared/lib/phone";
import { Badge, ButtonLink } from "@/shared/ui";

export default async function AccountPage() {
  await connection();
  const [me, orders, estimates] = await Promise.all([
    accountData<Customer>("account/me", "/account"),
    accountData<PaginatedOrders>("account/orders?page_size=3", "/account"),
    accountData<PaginatedEstimates>("account/estimates?page_size=3", "/account"),
  ]);
  return (
    <div className="flex flex-col gap-12">
      <div className="flex flex-col gap-3">
        <h1 className="t-h1" data-testid="account-greeting">{me.name ? `Вітаємо, ${me.name}` : "Кабінет"}</h1>
        <div className="flex flex-wrap items-center gap-3 text-text-muted">
          <span className="tabular">{formatPhone(me.phone)}</span>
          {me.is_master ? <Badge tone="accent"><span data-testid="master-badge">Майстер — особливі ціни</span></Badge> : null}
        </div>
      </div>
      <section aria-labelledby="last-orders" className="flex flex-col gap-4">
        <div className="flex items-baseline justify-between">
          <h2 id="last-orders" className="t-h3">Останні замовлення</h2>
          {orders.count > 0 ? <Link href="/account/orders" className="link t-small">Усі ({orders.count})</Link> : null}
        </div>
        {orders.results.length ? (
          <ul className="divide-y divide-line border-y border-line">
            {orders.results.map((o) => (
              <li key={o.public_token}>
                <Link href={`/orders/${o.public_token}`} className="flex justify-between gap-4 py-4 hover:text-accent-strong">
                  <span>№{o.number ?? "—"} · {o.status_label}</span>
                  <span className="tabular">{formatUah(o.total_kop)}</span>
                </Link>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-text-muted">Замовлень ще немає. <Link href="/catalog" className="link">До каталогу</Link></p>
        )}
      </section>
      <section aria-labelledby="last-estimates" className="flex flex-col gap-4">
        <div className="flex items-baseline justify-between">
          <h2 id="last-estimates" className="t-h3">Кошториси</h2>
          {estimates.count > 0 ? <Link href="/account/estimates" className="link t-small">Усі ({estimates.count})</Link> : null}
        </div>
        {estimates.results.length ? (
          <ul className="divide-y divide-line border-y border-line">
            {estimates.results.map((e) => (
              <li key={e.code}>
                <Link href={`/calculator/${e.code}`} className="flex justify-between gap-4 py-4 hover:text-accent-strong">
                  <span>{e.title || `Кошторис ${e.code}`}</span>
                  <span className="tabular">{formatUah(e.total_kop)}</span>
                </Link>
              </li>
            ))}
          </ul>
        ) : (
          <div className="flex flex-col items-start gap-4">
            <p className="text-text-muted">Збережені розрахунки з’являться тут.</p>
            <ButtonLink href="/calculator" variant="secondary" size="sm">Порахувати ремонт</ButtonLink>
          </div>
        )}
      </section>
    </div>
  );
}
