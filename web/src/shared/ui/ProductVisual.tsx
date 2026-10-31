import Image from "next/image";

import { mediaUrl } from "@/shared/lib/media";

import { TileSwatch } from "./TileSwatch";

/** Фото товару або зразок плитки. Пропорція 4:5, як у ТЗ. */
export function ProductVisual({
  image, name, size, color, sizes = "(min-width: 768px) 33vw, 50vw", priority, className,
}: {
  image?: string | null;
  name: string;
  size?: string | null;
  color?: string | null;
  sizes?: string;
  priority?: boolean;
  className?: string;
}) {
  const src = mediaUrl(image);
  const [w, h] = (size ?? "600x600").split("x").map(Number);
  return (
    <div className={`relative aspect-[4/5] overflow-hidden bg-surface ${className ?? ""}`}>
      {src ? (
        <Image src={src} alt={name} fill sizes={sizes} priority={priority}
          unoptimized={/^https?:\/\/(localhost|127\.)/.test(src)} className="img-zoom object-cover" />
      ) : (
        <TileSwatch width={w} height={h} color={color} className="img-zoom size-full" label={`Зразок: ${name}`} />
      )}
    </div>
  );
}
