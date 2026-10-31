import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { connection } from "next/server";

import { OrderStatusView, PayButton } from "@/features/orders";
import { ApiError } from "@/shared/api/errors";
import { serverFetch } from "@/shared/api/server";
import type { PublicOrder } from "@/shared/api/types";
import { Notice } from "@/shared/ui";

export const metadata: Metadata = { title: "Замовлення", robots: { index: false, follow: false } };

type Props = { params: Promise<{ token: string }>; searchParams: Promise<{ pay?: string; fake_payment?: string }> };

async function load(token: string): Promise<PublicOrder | null> {
  if (!/^[A-Za-z0-9_-]{8,64}$/.test(token)) return null;
  try {
    return await serverFetch<PublicOrder>(`orders/${token}`);
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) return null;
    throw e;
  }
}

export default async function OrderPage({ params, searchParams }: Props) {
  await connection();
  const { token } = await params;
  const { pay, fake_payment: fakePayment } = await searchParams;
  const order = await load(token);
  if (!order) notFound();
  const awaitingPayment = order.payment_method === "online" && order.payment_status !== "paid" && order.status !== "cancelled";
  return (
    <div className="container-page flex max-w-3xl flex-col gap-10 py-10 md:py-14">
      <div className="flex flex-col gap-3">
        <p className="t-label text-accent-strong">Дякуємо!</p>
        <h1 className="t-h1">Замовлення {order.number ? <span className="tabular" data-testid="order-number">№{order.number}</span> : null}</h1>
        <p className="text-text-muted">Збережіть посилання на цю сторінку — тут видно статус. Менеджер зателефонує, щоб підтвердити деталі.</p>
      </div>
      {pay === "retry" ? <Notice tone="warning">Оплата не пройшла. Спробуйте ще раз або оберіть оплату при отриманні — напишіть менеджеру.</Notice> : null}
      {fakePayment && awaitingPayment ? (
        <div data-testid="fake-payment"><Notice tone="info">
          Тестовий режим оплати: справжня платіжна система не підключена. Статус зміниться після сигналу від платіжного сервісу.
        </Notice></div>
      ) : null}
      {awaitingPayment ? <PayButton token={order.public_token} /> : null}
      <OrderStatusView order={order} />
    </div>
  );
}
