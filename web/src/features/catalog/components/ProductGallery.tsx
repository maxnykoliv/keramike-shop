"use client";

import Image from "next/image";
import { useState } from "react";

import type { ProductImage } from "@/shared/api/types";
import { mediaUrl } from "@/shared/lib/media";
import { Dialog, ProductVisual } from "@/shared/ui";

/** Галерея: текстура, інтер'єр, збільшення на весь екран. Без фото — зразок плитки. */
export function ProductGallery({ images, name, size, color }: { images: ProductImage[]; name: string; size?: string | null; color?: string }) {
  const [active, setActive] = useState(0);
  const [zoom, setZoom] = useState(false);
  if (images.length === 0) return <ProductVisual name={name} size={size} color={color} priority sizes="(min-width: 768px) 50vw, 100vw" />;
  const current = images[active] ?? images[0]!;
  const src = mediaUrl(current.urls.lg) ?? "";
  return (
    <div className="flex flex-col gap-3">
      <button type="button" onClick={() => setZoom(true)} className="group block" aria-label="Збільшити фото">
        <ProductVisual image={current.urls.md} name={current.alt || name} priority sizes="(min-width: 768px) 50vw, 100vw" />
      </button>
      {images.length > 1 ? (
        <ul className="flex snap-x gap-3 overflow-x-auto" aria-label="Фото товару">
          {images.map((img, i) => (
            <li key={img.urls.sm} className="w-20 shrink-0 snap-start">
              <button type="button" onClick={() => setActive(i)} aria-current={i === active}
                aria-label={`Фото ${i + 1}${img.kind === "interior" ? ", в інтер'єрі" : ""}`}
                className={i === active ? "outline outline-1 outline-text" : ""}>
                <ProductVisual image={img.urls.sm} name={img.alt || name} sizes="80px" />
              </button>
            </li>
          ))}
        </ul>
      ) : null}
      <Dialog open={zoom} onOpenChange={setZoom} title={name}>
        <div className="relative aspect-square w-full">
          <Image src={src} alt={current.alt || name} fill sizes="100vw" className="object-contain"
            unoptimized={/^https?:\/\/(localhost|127\.)/.test(src)} />
        </div>
      </Dialog>
    </div>
  );
}
