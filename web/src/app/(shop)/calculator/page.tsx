import type { Metadata } from "next";

import { CalculatorView } from "@/features/calculator";

export const metadata: Metadata = {
  title: "Калькулятор ремонту",
  description: "Порахуйте плитку, клей, затирку й роботу для ванної, кухні чи тераси. Результат — у кошик одним кліком.",
  alternates: { canonical: "/calculator" },
};

type Props = { searchParams: Promise<{ product?: string; estimate?: string }> };

const SLUG = /^[a-z0-9-]{1,120}$/;
const CODE = /^[A-Za-z0-9]{4,32}$/;

export default async function CalculatorPage({ searchParams }: Props) {
  const { product, estimate } = await searchParams;
  return (
    <div className="container-page flex flex-col gap-10 py-10 md:py-14">
      <div className="flex max-w-2xl flex-col gap-4">
        <p className="t-label text-accent-strong">Калькулятор</p>
        <h1 className="t-h1">Скільки коштуватиме ремонт</h1>
        <p className="text-text-muted">Розрахунок орієнтовний. Остаточну суму підтвердить менеджер після замовлення.</p>
      </div>
      <CalculatorView
        productSlug={product && SLUG.test(product) ? product : undefined}
        estimateCode={estimate && CODE.test(estimate) ? estimate : undefined}
      />
    </div>
  );
}
