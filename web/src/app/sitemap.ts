import type { MetadataRoute } from "next";
import { connection } from "next/server";

import { serverEnv } from "@/env";
import { getCategories } from "@/features/catalog/server";
import { publicGet } from "@/shared/api/server";
import type { CategoryNode, PaginatedProducts } from "@/shared/api/types";

const flatten = (nodes: CategoryNode[]): CategoryNode[] => nodes.flatMap((n) => [n, ...flatten(n.children)]);

async function allProductSlugs(): Promise<string[]> {
  const slugs: string[] = [];
  for (let page = 1; page <= 50; page++) {
    const data = await publicGet<PaginatedProducts>(`catalog/products?page=${page}&page_size=100`);
    slugs.push(...data.results.map((p) => p.slug));
    if (!data.next) break;
  }
  return slugs;
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  await connection();
  const site = serverEnv().SITE_URL;
  const pages = ["", "/catalog", "/calculator", "/delivery", "/contacts", "/about"].map((path) => ({
    url: `${site}${path}`, changeFrequency: "weekly" as const, priority: path === "" ? 1 : 0.7,
  }));
  const [categories, products] = await Promise.all([
    getCategories().then(flatten).catch(() => []),
    allProductSlugs().catch(() => []),
  ]);
  return [
    ...pages,
    ...categories.map((c) => ({ url: `${site}/catalog/${c.slug}`, changeFrequency: "weekly" as const, priority: 0.8 })),
    ...products.map((slug) => ({ url: `${site}/product/${slug}`, changeFrequency: "weekly" as const, priority: 0.6 })),
  ];
}
