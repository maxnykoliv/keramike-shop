"use client";

import Link from "next/link";

import { Icon } from "@/shared/ui";

import { cartCount, useCart } from "../hooks/useCart";

export function CartCount() {
  const { data } = useCart();
  const count = cartCount(data);
  return (
    <Link href="/cart" className="relative grid size-11 place-items-center" aria-label={`Кошик, позицій: ${count}`}>
      <Icon name="cart" size={22} />
      {count > 0 ? (
        <span data-testid="cart-count"
          className="tabular absolute top-1 right-0 grid min-w-5 place-items-center rounded-full bg-button px-1 text-[11px] leading-5 text-bg">
          {count}
        </span>
      ) : null}
    </Link>
  );
}
