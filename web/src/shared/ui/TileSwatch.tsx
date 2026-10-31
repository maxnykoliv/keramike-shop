import { swatchColors } from "@/shared/lib/swatch";

/**
 * A tile swatch until there is a photo: the color from the specs and a joint grid in the tile's proportions.
 * It conveys both color and size (60×60 shows squares, 30×60 shows bricks).
 */
export function TileSwatch({
  width = 600, height = 600, color, className, label,
}: { width?: number; height?: number; color?: string | null; className?: string; label?: string }) {
  const [base, joint] = swatchColors(color);
  const ratio = Math.max(0.2, Math.min(5, width / height));
  const cell = 100;
  const tileW = ratio >= 1 ? cell * Math.min(ratio, 2) : cell;
  const tileH = ratio >= 1 ? cell : cell / Math.max(ratio, 0.5);
  const cols = Math.ceil(400 / tileW) + 1;
  const rows = Math.ceil(500 / tileH) + 1;
  const offset = ratio >= 1.5 ? tileW / 2 : 0;
  const lines: string[] = [];
  for (let r = 0; r <= rows; r++) lines.push(`M0 ${r * tileH}H400`);
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c <= cols; c++) {
      const x = c * tileW - (r % 2 ? offset : 0);
      lines.push(`M${x} ${r * tileH}V${(r + 1) * tileH}`);
    }
  }
  return (
    <svg viewBox="0 0 400 500" preserveAspectRatio="xMidYMid slice" className={className}
      role={label ? "img" : undefined} aria-label={label} aria-hidden={label ? undefined : true}>
      <rect width="400" height="500" fill={base} />
      <path d={lines.join(" ")} stroke={joint} strokeWidth="2" fill="none" />
    </svg>
  );
}
