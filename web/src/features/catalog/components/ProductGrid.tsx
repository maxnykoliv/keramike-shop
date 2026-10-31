"use client";

import { useState } from "react";

import { bff } from "@/shared/api/client";
import { friendlyMessage } from "@/shared/api/errors";
import type { PaginatedProducts, ProductCard as Product } from "@/shared/api/types";
import { pluralUk } from "@/shared/lib/numbers";
import { Button, Notice } from "@/shared/ui";

import { usePersonalPrices } from "../hooks/usePersonalPrices";
import { ProductCard } from "./ProductCard";

/**
 * Сітка товарів із «Показати ще». Номер сторінки пишемо в адресу без перезавантаження,
 * тож після оновлення сторінки показане не губиться.
 */
export function ProductGrid({
  initial, query, page = 1, pageSize = 24,
}: { initial: PaginatedProducts | { results: Product[]; next?: null; count?: number }; query?: string; page?: number; pageSize?: number }) {
  const [products, setProducts] = useState(initial.results);
  const [hasNext, setHasNext] = useState(Boolean(initial.next));
  const [current, setCurrent] = useState(page);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { isMaster, priceOf } = usePersonalPrices(products.map((p) => p.id));

  const loadMore = async () => {
    setLoading(true);
    setError(null);
    try {
      const nextPage = current + 1;
      const q = new URLSearchParams(query ?? "");
      q.set("page", String(nextPage));
      q.set("page_size", String(pageSize));
      const data = await bff<PaginatedProducts>(`catalog/products?${q}`);
      setProducts((prev) => [...prev, ...data.results]);
      setHasNext(Boolean(data.next));
      setCurrent(nextPage);
      const url = new URL(window.location.href);
      url.searchParams.set("page", String(nextPage));
      window.history.replaceState(null, "", url);
    } catch (e) {
      setError(friendlyMessage(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-10">
      <ul className="grid grid-cols-2 gap-x-4 gap-y-10 md:grid-cols-3 md:gap-x-8 md:gap-y-14" data-testid="product-grid">
        {products.map((product) => (
          <li key={product.id}>
            <ProductCard product={product} priceKop={isMaster ? priceOf(product.id, product.price_kop) : undefined} />
          </li>
        ))}
      </ul>
      {error ? <Notice tone="error">{error}</Notice> : null}
      {hasNext ? (
        <div className="flex flex-col items-center gap-2">
          <p className="t-small text-text-muted" aria-live="polite">
            Показано {products.length} {pluralUk(products.length, ["товар", "товари", "товарів"])}
            {"count" in initial && initial.count ? ` з ${initial.count}` : ""}
          </p>
          <Button variant="secondary" onClick={loadMore} loading={loading}>Показати ще</Button>
        </div>
      ) : null}
    </div>
  );
}
