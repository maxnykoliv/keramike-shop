import type { Metadata } from "next";

import { LoginPanel } from "@/features/auth";

export const metadata: Metadata = { title: "Вхід", robots: { index: false } };

type Props = { searchParams: Promise<{ next?: string }> };

/** Повертаємо лише на свої сторінки: «//evil.com» і повні адреси відкидаємо. */
function safeNext(value: string | undefined): string {
  if (!value || !value.startsWith("/") || value.startsWith("//") || value.startsWith("/\\")) return "/account";
  return value;
}

export default async function LoginPage({ searchParams }: Props) {
  const next = safeNext((await searchParams).next);
  return (
    <div className="container-page flex max-w-md flex-col gap-8 py-12 md:py-20">
      <div className="flex flex-col gap-3">
        <h1 className="t-h1">Вхід</h1>
        <p className="text-text-muted">Без пароля: підтвердіть номер у Telegram або кодом. Історія замовлень і кошторисів — у кабінеті.</p>
      </div>
      <LoginPanel next={next} />
    </div>
  );
}
