import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { connection } from "next/server";

import { ProductGallery, ProductGrid, ProductPurchase, SpecsTable } from "@/features/catalog";
import { getProduct } from "@/features/catalog/server";
import type { ProductCard } from "@/shared/api/types";
import { tileSpecOf } from "@/shared/api/types";
import { mediaUrl } from "@/shared/lib/media";
import { Breadcrumbs } from "@/shared/ui";

type Props = { params: Promise<{ slug: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const product = await getProduct((await params).slug).catch(() => null);
  if (!product) return { title: "Товар не знайдено" };
  const image = mediaUrl(product.image);
  return {
    title: product.seo_title || product.name,
    description: product.seo_description || `${product.name} — ${product.price_display}. Розрахунок упаковок і доставка по Україні.`,
    alternates: { canonical: `/product/${product.slug}` },
    openGraph: { title: product.name, images: image ? [image] : undefined },
  };
}

export default async function ProductPage({ params }: Props) {
  await connection();
  const product = await getProduct((await params).slug);
  if (!product) notFound();
  const spec = tileSpecOf(product);
  const related = [...(product.related.same_collection ?? []), ...(product.related.recommended ?? [])] as unknown as ProductCard[];
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Product",
    name: product.name,
    sku: product.sku,
    brand: product.manufacturer ? { "@type": "Brand", name: product.manufacturer } : undefined,
    image: mediaUrl(product.image) ?? undefined,
    offers: {
      "@type": "Offer",
      priceCurrency: "UAH",
      price: (product.price_kop / 100).toFixed(2),
      availability: product.stock_status === "out_of_stock" ? "https://schema.org/OutOfStock" : "https://schema.org/InStock",
    },
  };
  return (
    <div className="container-page flex flex-col gap-10 py-10 md:py-14">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c") }} />
      <Breadcrumbs items={[
        { href: "/", label: "Головна" },
        { href: "/catalog", label: "Каталог" },
        { href: `/catalog/${product.category.slug}`, label: product.category.name ?? "" },
        { label: product.name },
      ]} />
      <div className="grid gap-10 md:grid-cols-[1.2fr_1fr] md:gap-16">
        <ProductGallery images={product.images} name={product.name} size={product.size} color={spec?.color} />
        <div className="flex flex-col gap-8">
          <div className="flex flex-col gap-3">
            {product.collection ? (
              <Link href={`/catalog?collection=${product.collection.slug}`} className="t-label text-accent-strong">
                {product.collection.name}
              </Link>
            ) : null}
            <h1 className="t-h1" data-testid="product-title">{product.name}</h1>
            <p className="t-small text-text-muted">Артикул {product.sku}{product.manufacturer ? ` · ${product.manufacturer}` : ""}</p>
          </div>
          <ProductPurchase product={product} />
        </div>
      </div>
      <div className="grid gap-10 md:grid-cols-2 md:gap-16">
        {product.description ? (
          <section aria-labelledby="about-title">
            <h2 id="about-title" className="t-h3 mb-4">Опис</h2>
            <p className="whitespace-pre-line text-text-muted">{product.description}</p>
          </section>
        ) : null}
        <section aria-labelledby="specs-title">
          <h2 id="specs-title" className="t-h3 mb-4">Характеристики</h2>
          <SpecsTable product={product} />
        </section>
      </div>
      {related.length > 0 ? (
        <section aria-labelledby="related-title" className="pt-10">
          <h2 id="related-title" className="t-h2 mb-8">Пасує до цього</h2>
          <ProductGrid initial={{ results: related.slice(0, 6), next: null }} />
        </section>
      ) : null}
    </div>
  );
}
