import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { connection } from "next/server";

import { EstimateActions } from "@/features/calculator";
import { ApiError } from "@/shared/api/errors";
import { serverFetch } from "@/shared/api/server";
import type { EstimateDetail } from "@/shared/api/types";
import { formatUah } from "@/shared/lib/money";
import { formatDecimal, unitLabel } from "@/shared/lib/numbers";
import { Breadcrumbs, Notice } from "@/shared/ui";

export const metadata: Metadata = { title: "Кошторис", robots: { index: false, follow: false } };

type Props = { params: Promise<{ code: string }> };

async function load(code: string): Promise<EstimateDetail | null> {
  if (!/^[A-Za-z0-9]{4,32}$/.test(code)) return null;
  try {
    return await serverFetch<EstimateDetail>(`calc/estimates/${code}`);
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) return null;
    throw e;
  }
}

export default async function EstimatePage({ params }: Props) {
  await connection();
  const { code } = await params;
  const estimate = await load(code);
  if (!estimate) notFound();
  const result = estimate.current ?? estimate.result;
  const created = new Date(estimate.created_at).toLocaleDateString("uk-UA", { day: "numeric", month: "long", year: "numeric" });
  return (
    <div className="container-page flex flex-col gap-10 py-10 md:py-14">
      <Breadcrumbs items={[{ href: "/", label: "Головна" }, { href: "/calculator", label: "Калькулятор" }, { label: `Кошторис ${code}` }]} />
      <div className="flex flex-col gap-3">
        <h1 className="t-h1">Кошторис <span className="tabular" data-testid="estimate-code">{code}</span></h1>
        <p className="text-text-muted">Збережено {created}</p>
      </div>
      {estimate.changed ? (
        <Notice tone="warning">
          Відтоді ціни змінилися: було {formatUah(estimate.result.total_kop)}, зараз {formatUah(result.total_kop)}.
        </Notice>
      ) : null}
      <div className="grid gap-12 md:grid-cols-[1fr_360px] md:items-start">
        <section aria-labelledby="lines-title">
          <h2 id="lines-title" className="t-h3 mb-4">Склад</h2>
          <ul className="divide-y divide-line border-y border-line" data-testid="estimate-lines">
            {result.lines.map((line, i) => (
              <li key={`${line.kind}-${i}`} className="flex justify-between gap-4 py-4">
                <div>
                  <p>{line.name}</p>
                  <p className="t-small tabular text-text-muted">{formatDecimal(line.quantity)} {unitLabel(line.unit)}</p>
                </div>
                <p className="tabular shrink-0">{formatUah(line.total_kop)}</p>
              </li>
            ))}
          </ul>
          <div className="mt-6 flex items-baseline justify-between">
            <span className="font-semibold">Разом</span>
            <span className="t-price" data-testid="estimate-total">{formatUah(result.total_kop)}</span>
          </div>
        </section>
        <EstimateActions code={code} canAddToCart={result.lines.some((l) => l.product_id)} />
      </div>
    </div>
  );
}
