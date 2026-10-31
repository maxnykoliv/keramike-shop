"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { useCartActions } from "@/features/cart";
import { friendlyMessage } from "@/shared/api/errors";
import type { OrderItem } from "@/shared/api/types";
import { Button, Notice } from "@/shared/ui";

/** Reorder: the lines go into the cart at current prices. */
export function ReorderButton({ items }: { items: OrderItem[] }) {
  const router = useRouter();
  const { add } = useCartActions();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const available = items.filter((i) => i.product_id);
  const reorder = async () => {
    setBusy(true);
    setError(null);
    try {
      for (const item of available) await add.mutateAsync({ product_id: item.product_id!, qty: item.qty });
      router.push("/cart");
    } catch (e) {
      setError(friendlyMessage(e));
      setBusy(false);
    }
  };
  if (available.length === 0) return null;
  return (
    <div className="flex flex-col gap-2">
      <Button variant="secondary" size="sm" onClick={reorder} loading={busy}>Повторити</Button>
      {error ? <Notice tone="error">{error}</Notice> : null}
    </div>
  );
}
