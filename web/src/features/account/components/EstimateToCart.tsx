"use client";

import { useRouter } from "next/navigation";

import { useCartActions } from "@/features/cart";
import { Button } from "@/shared/ui";

export function EstimateToCart({ code }: { code: string }) {
  const router = useRouter();
  const { fromEstimate } = useCartActions();
  return (
    <Button variant="ghost" size="sm" loading={fromEstimate.isPending}
      onClick={async () => { await fromEstimate.mutateAsync(code); router.push("/cart"); }}>
      У кошик
    </Button>
  );
}
