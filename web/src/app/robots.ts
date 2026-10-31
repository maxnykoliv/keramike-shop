import type { MetadataRoute } from "next";
import { connection } from "next/server";

import { serverEnv } from "@/env";

export default async function robots(): Promise<MetadataRoute.Robots> {
  await connection();
  const site = serverEnv().SITE_URL;
  return {
    rules: [{ userAgent: "*", allow: "/", disallow: ["/api/", "/account", "/cart", "/checkout", "/orders/", "/login", "/search"] }],
    sitemap: `${site}/sitemap.xml`,
  };
}
