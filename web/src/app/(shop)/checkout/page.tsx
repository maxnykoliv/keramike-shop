import type { Metadata } from "next";

import { CheckoutForm } from "@/features/checkout";

export const metadata: Metadata = { title: "Оформлення замовлення", robots: { index: false } };

export default function CheckoutPage() {
  return (
    <div className="container-page flex flex-col gap-10 py-10 md:py-14">
      <h1 className="t-h1">Оформлення</h1>
      <CheckoutForm />
    </div>
  );
}
