import type { Metadata } from "next";
import { connection } from "next/server";

import { ProductGrid } from "@/features/catalog";
import { searchProducts } from "@/features/catalog/server";
import { Notice } from "@/shared/ui";

export const metadata: Metadata = { title: "Пошук", robots: { index: false } };

type Props = { searchParams: Promise<{ q?: string }> };

export default async function SearchPage({ searchParams }: Props) {
  await connection();
  const q = ((await searchParams).q ?? "").trim().slice(0, 100);
  const results = q.length >= 2 ? await searchProducts(q).catch(() => null) : [];
  return (
    <div className="container-page flex flex-col gap-8 py-10 md:py-14">
      <h1 className="t-h1">Пошук</h1>
      <form role="search" action="/search" className="flex max-w-xl gap-3">
        <label htmlFor="q" className="sr-only">Що шукаємо</label>
        <input id="q" name="q" type="search" defaultValue={q} minLength={2} placeholder="Назва, артикул, колекція"
          className="min-h-12 flex-1 border-b border-line-strong bg-transparent text-lg focus:outline-none" />
        <button type="submit" className="t-label min-h-12 bg-button px-6 text-bg">Знайти</button>
      </form>
      {results === null ? <Notice tone="error">Пошук тимчасово не працює.</Notice> : null}
      {q.length >= 2 && results ? (
        results.length ? (
          <>
            <p className="t-small text-text-muted" data-testid="search-count">Знайдено: {results.length}</p>
            <ProductGrid initial={{ results, next: null }} />
          </>
        ) : (
          <p className="text-text-muted" data-testid="search-empty">За запитом «{q}» нічого не знайшли.</p>
        )
      ) : null}
    </div>
  );
}
