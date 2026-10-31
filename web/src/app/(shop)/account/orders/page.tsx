import type { Metadata } from "next";
import Link from "next/link";
import { connection } from "next/server";

import { ReorderButton } from "@/features/account";
import { accountData } from "@/features/account/server";
import type { PaginatedOrders } from "@/shared/api/types";
import { formatUah } from "@/shared/lib/money";
import { Badge } from "@/shared/ui";

export const metadata: Metadata = { title: "Замовлення" };

type Props = { searchParams: Promise<{ page?: string }> };

export default async function AccountOrdersPage({ searchParams }: Props) {
  await connection();
  const page = Math.max(1, Number((await searchParams).page) || 1);
  const data = await accountData<PaginatedOrders>(`account/orders?page=${page}&page_size=20`, "/account/orders");
  return (
    <div className="flex flex-col gap-8">
      <h1 className="t-h2">Замовлення</h1>
      {data.results.length === 0 ? (
        <p className="text-text-muted" data-testid="orders-empty">Замовлень ще немає. <Link className="link" href="/catalog">До каталогу</Link></p>
      ) : (
        <ul className="flex flex-col gap-4" data-testid="orders-list">
          {data.results.map((order) => (
            <li key={order.public_token} className="flex flex-col gap-4 border border-line p-5">
              <div className="flex flex-wrap items-baseline justify-between gap-3">
                <Link href={`/orders/${order.public_token}`} className="t-h3 hover:text-accent-strong">№{order.number ?? "—"}</Link>
                <span className="t-price">{formatUah(order.total_kop)}</span>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <Badge>{order.status_label}</Badge>
                <Badge tone={order.payment_status === "paid" ? "success" : "neutral"}>{order.payment_status_label}</Badge>
                <span className="t-small text-text-muted">{new Date(order.created_at).toLocaleDateString("uk-UA")}</span>
              </div>
              <p className="t-small text-text-muted">{order.items.map((i) => i.name).join(", ")}</p>
              <ReorderButton items={order.items} />
            </li>
          ))}
        </ul>
      )}
      <nav aria-label="Сторінки" className="flex gap-4">
        {data.previous ? <Link className="link" href={`/account/orders?page=${page - 1}`}>← Новіші</Link> : null}
        {data.next ? <Link className="link" href={`/account/orders?page=${page + 1}`}>Старіші →</Link> : null}
      </nav>
    </div>
  );
}
