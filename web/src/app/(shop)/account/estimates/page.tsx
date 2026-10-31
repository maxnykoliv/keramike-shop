import type { Metadata } from "next";
import Link from "next/link";
import { connection } from "next/server";

import { EstimateToCart } from "@/features/account";
import { accountData } from "@/features/account/server";
import type { PaginatedEstimates } from "@/shared/api/types";
import { formatUah } from "@/shared/lib/money";
import { ButtonLink } from "@/shared/ui";

export const metadata: Metadata = { title: "Кошториси" };

export default async function AccountEstimatesPage() {
  await connection();
  const data = await accountData<PaginatedEstimates>("account/estimates?page_size=50", "/account/estimates");
  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-wrap items-baseline justify-between gap-4">
        <h1 className="t-h2">Кошториси</h1>
        <ButtonLink href="/calculator" size="sm" variant="secondary">Новий розрахунок</ButtonLink>
      </div>
      {data.results.length === 0 ? (
        <p className="text-text-muted" data-testid="estimates-empty">Збережених кошторисів ще немає.</p>
      ) : (
        <ul className="divide-y divide-line border-y border-line" data-testid="estimates-list">
          {data.results.map((e) => (
            <li key={e.code} className="flex flex-wrap items-center justify-between gap-4 py-4">
              <div>
                <Link href={`/calculator/${e.code}`} className="hover:text-accent-strong">{e.title || `Кошторис ${e.code}`}</Link>
                <p className="t-small text-text-muted">{e.code} · {new Date(e.created_at).toLocaleDateString("uk-UA")}</p>
              </div>
              <div className="flex items-center gap-4">
                <span className="tabular">{formatUah(e.total_kop)}</span>
                <EstimateToCart code={e.code} />
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
