"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { request } from "@/shared/api/client";
import type { Cart } from "@/shared/api/types";
import { track } from "@/shared/lib/analytics";

export const CART_KEY = ["cart"] as const;

export function useCart() {
  return useQuery({ queryKey: CART_KEY, queryFn: () => request<Cart>("/api/cart"), staleTime: 30_000 });
}

export function useCartActions() {
  const client = useQueryClient();
  const setCart = (cart: Cart) => client.setQueryData(CART_KEY, cart);

  const add = useMutation({
    mutationFn: (item: { product_id: number; qty: number; group_label?: string }) =>
      request<Cart>("/api/cart/items", { method: "POST", body: item }),
    onSuccess: (cart, item) => {
      setCart(cart);
      track("add_to_cart", { product_id: item.product_id, qty: item.qty });
    },
  });
  const update = useMutation({
    mutationFn: ({ id, qty }: { id: number; qty: number }) =>
      request<Cart>(`/api/cart/items/${id}`, { method: "PATCH", body: { qty } }),
    onMutate: async ({ id, qty }) => {
      // Update the counter optimistically; the server corrects the totals afterwards.
      await client.cancelQueries({ queryKey: CART_KEY });
      const previous = client.getQueryData<Cart>(CART_KEY);
      if (previous) setCart({ ...previous, lines: previous.lines.map((l) => (l.id === id ? { ...l, qty } : l)) });
      return { previous };
    },
    onError: (_e, _v, ctx) => ctx?.previous && setCart(ctx.previous),
    onSuccess: setCart,
  });
  const remove = useMutation({
    mutationFn: (id: number) => request<Cart>(`/api/cart/items/${id}`, { method: "DELETE" }),
    onSuccess: setCart,
  });
  const fromEstimate = useMutation({
    mutationFn: (code: string) => request<Cart>(`/api/cart/from-estimate/${code}`, { method: "POST" }),
    onSuccess: (cart) => {
      setCart(cart);
      track("add_to_cart", { source: "estimate" });
    },
  });
  return { add, update, remove, fromEstimate };
}

export const cartCount = (cart: Cart | undefined) => cart?.lines.length ?? 0;
