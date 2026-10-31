import "server-only";

import { ApiError } from "@/shared/api/errors";
import { publicGet } from "@/shared/api/server";
import type { CategoryNode, Facets, PaginatedProducts, ProductCard, ProductDetail } from "@/shared/api/types";

export const PAGE_SIZE = 24;

/** Filter params the backend accepts. Everything else in the page URL is dropped. */
export const FILTER_KEYS = ["kind", "application", "room", "size", "color", "surface", "material",
  "manufacturer", "collection", "price_min", "price_max", "in_stock", "ordering"] as const;

export type SearchParams = Record<string, string | string[] | undefined>;

export function filterQuery(params: SearchParams, category?: string): URLSearchParams {
  const q = new URLSearchParams();
  for (const key of FILTER_KEYS) {
    const value = params[key];
    for (const v of Array.isArray(value) ? value : value ? [value] : []) q.append(key, v);
  }
  if (category) q.set("category", category);
  return q;
}

export async function getProducts(query: URLSearchParams, page = 1): Promise<PaginatedProducts> {
  const q = new URLSearchParams(query);
  q.set("page", String(page));
  q.set("page_size", String(PAGE_SIZE));
  return publicGet<PaginatedProducts>(`catalog/products?${q}`);
}

/** Pages 1..page: after a reload, "Show more" restores what was already shown. */
export async function getProductPages(query: URLSearchParams, page: number): Promise<PaginatedProducts> {
  const pages = Math.max(1, Math.min(page, 5));
  const results = await Promise.all(Array.from({ length: pages }, (_, i) => getProducts(query, i + 1).catch((e) => {
    if (e instanceof ApiError && e.status === 404) return null;
    throw e;
  })));
  const valid = results.filter(Boolean) as PaginatedProducts[];
  const last = valid.at(-1);
  return {
    count: valid[0]?.count ?? 0,
    next: last?.next ?? null,
    previous: null,
    results: valid.flatMap((p) => p.results),
  };
}

export const getFacets = (query: URLSearchParams) => publicGet<Facets>(`catalog/facets?${query}`);

export const getCategories = () => publicGet<CategoryNode[]>("catalog/categories");

export async function getProduct(slug: string): Promise<ProductDetail | null> {
  try {
    return await publicGet<ProductDetail>(`catalog/products/${encodeURIComponent(slug)}`, ["catalog", `product:${slug}`]);
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) return null;
    throw e;
  }
}

export const searchProducts = (q: string) =>
  publicGet<ProductCard[]>(`catalog/search?q=${encodeURIComponent(q)}`);

export function findCategory(tree: CategoryNode[], slug: string): CategoryNode | null {
  for (const node of tree) {
    if (node.slug === slug) return node;
    const child = findCategory(node.children, slug);
    if (child) return child;
  }
  return null;
}
