import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { connection } from "next/server";

import { CatalogFilters, CatalogToolbar, ProductGrid } from "@/features/catalog";
import {
  PAGE_SIZE, filterQuery, findCategory, getCategories, getFacets, getProductPages, type SearchParams,
} from "@/features/catalog/server";
import { Breadcrumbs, Notice } from "@/shared/ui";

type Props = { params: Promise<{ category?: string[] }>; searchParams: Promise<SearchParams> };

export async function generateMetadata({ params, searchParams }: Props): Promise<Metadata> {
  const { category } = await params;
  const sp = await searchParams;
  const slug = category?.[0];
  const node = slug ? findCategory(await getCategories().catch(() => []), slug) : null;
  const title = node?.name ?? "Каталог плитки";
  const filtered = Object.keys(sp).some((k) => k !== "page");
  return {
    title,
    description: `${title}: ціни, наявність, розрахунок кількості упаковок онлайн.`,
    alternates: { canonical: slug ? `/catalog/${slug}` : "/catalog" },
    // Filter combinations are not indexed, only categories.
    robots: filtered ? { index: false, follow: true } : undefined,
  };
}

export default async function CatalogPage({ params, searchParams }: Props) {
  await connection();
  const { category } = await params;
  const sp = await searchParams;
  if ((category?.length ?? 0) > 1) notFound();
  const slug = category?.[0];
  const tree = await getCategories().catch(() => []);
  const node = slug ? findCategory(tree, slug) : null;
  if (slug && !node) notFound();

  const query = filterQuery(sp, slug);
  const page = Math.max(1, Number(sp.page) || 1);
  const [products, facets] = await Promise.all([
    getProductPages(query, page).catch(() => null),
    getFacets(query).catch(() => null),
  ]);

  return (
    <div className="container-page flex flex-col gap-8 py-10 md:py-14">
      <Breadcrumbs items={[{ href: "/", label: "Головна" }, ...(node ? [{ href: "/catalog", label: "Каталог" }, { label: node.name }] : [{ label: "Каталог" }])]} />
      <h1 className="t-h1">{node?.name ?? "Каталог"}</h1>
      {tree.length > 0 ? (
        <nav aria-label="Категорії" className="-mx-4 overflow-x-auto px-4">
          <ul className="flex gap-2">
            {tree.map((c) => (
              <li key={c.slug}>
                <a href={`/catalog/${c.slug}`} aria-current={c.slug === slug ? "page" : undefined}
                  className={`t-small inline-flex min-h-10 items-center whitespace-nowrap border px-4 ${c.slug === slug ? "border-text bg-text text-bg" : "border-line hover:border-text"}`}>
                  {c.name}
                </a>
              </li>
            ))}
          </ul>
        </nav>
      ) : null}
      {!products || !facets ? (
        <Notice tone="error">Не вдалося завантажити каталог. Оновіть сторінку за хвилину.</Notice>
      ) : (
        <div className="grid gap-10 md:grid-cols-[240px_1fr] md:gap-12">
          <CatalogFilters facets={facets} />
          <div className="flex flex-col gap-8">
            <CatalogToolbar facets={facets} count={products.count} />
            {products.results.length === 0 ? (
              <p className="py-16 text-center text-text-muted" data-testid="empty-catalog">За цими фільтрами нічого немає. Спробуйте прибрати частину.</p>
            ) : (
              <ProductGrid key={query.toString()} initial={products} query={query.toString()} page={Math.min(page, 5)} pageSize={PAGE_SIZE} />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
