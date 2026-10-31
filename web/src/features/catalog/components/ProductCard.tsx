import Link from "next/link";

import type { ProductCard as Product } from "@/shared/api/types";
import { Price, ProductVisual } from "@/shared/ui";

const STOCK: Record<string, string> = { on_order: "Під замовлення", out_of_stock: "Немає в наявності" };

/** Велика картка без рамки: фото 4:5, назва, розмір, ціна за м². Вся картка — посилання. */
export function ProductCard({ product, priceKop }: { product: Product; priceKop?: number }) {
  const price = priceKop ?? product.price_kop;
  return (
    <article className="group relative flex flex-col gap-3" data-testid="product-card">
      <ProductVisual image={product.image} name={product.name} size={product.size} />
      <div className="flex flex-col gap-1">
        <h3 className="font-medium">
          <Link href={`/product/${product.slug}`} className="after:absolute after:inset-0">{product.name}</Link>
        </h3>
        <p className="t-small text-text-muted">
          {[product.size?.replace("x", "×"), product.manufacturer].filter(Boolean).join(" · ")}
        </p>
        <Price kop={price} retailKop={priceKop != null ? product.price_kop : null} unit={product.unit} />
        {STOCK[product.stock_status ?? "in_stock"] ? <p className="t-small text-text-muted">{STOCK[product.stock_status ?? "in_stock"]}</p> : null}
      </div>
    </article>
  );
}
