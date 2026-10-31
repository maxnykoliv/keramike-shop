import type { Metadata } from "next";

import { CartView } from "@/features/cart";

export const metadata: Metadata = { title: "Кошик", robots: { index: false } };

export default function CartPage() {
  return (
    <div className="container-page flex flex-col gap-10 py-10 md:py-14">
      <h1 className="t-h1">Кошик</h1>
      <CartView />
    </div>
  );
}
