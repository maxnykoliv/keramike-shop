import type { MaterialSpec, ProductDetail, TileSpec } from "@/shared/api/types";
import { formatDecimal } from "@/shared/lib/numbers";

import { APPLICATION_LABELS, MATERIAL_LABELS, ROOM_LABELS } from "../labels";

export function SpecsTable({ product }: { product: ProductDetail }) {
  const tile = product.tile_spec as unknown as TileSpec | null;
  const material = product.material_spec as unknown as MaterialSpec | null;
  const rows: [string, string][] = [["Артикул", product.sku]];
  if (product.manufacturer) rows.push(["Виробник", product.manufacturer]);
  if (product.collection) rows.push(["Колекція", (product.collection as { name: string }).name]);
  if (tile) {
    rows.push(
      ["Розмір", `${tile.width_mm} × ${tile.height_mm} мм`],
      ["Товщина", `${tile.thickness_mm} мм`],
      ["В упаковці", `${formatDecimal(tile.m2_per_pack)} м²${tile.pcs_per_pack ? `, ${tile.pcs_per_pack} шт` : ""}`],
    );
    if (tile.pack_weight_kg) rows.push(["Вага упаковки", `${formatDecimal(tile.pack_weight_kg)} кг`]);
    rows.push(["Матеріал", MATERIAL_LABELS[tile.material] ?? tile.material]);
    if (tile.surface) rows.push(["Поверхня", tile.surface]);
    if (tile.color) rows.push(["Колір", tile.color]);
    if (tile.applications.length) rows.push(["Призначення", tile.applications.map((a) => APPLICATION_LABELS[a] ?? a).join(", ")]);
    if (tile.rooms.length) rows.push(["Приміщення", tile.rooms.map((r) => ROOM_LABELS[r] ?? r).join(", ")]);
  }
  if (material) {
    rows.push(["Упаковка", `${formatDecimal(material.pack_size)} ${material.pack_unit === "l" ? "л" : "кг"}`]);
    if (material.consumption_hint) rows.push(["Витрата", material.consumption_hint]);
  }
  return (
    <dl className="divide-y divide-line border-y border-line" data-testid="specs">
      {rows.map(([label, value]) => (
        <div key={label} className="grid grid-cols-2 gap-4 py-3">
          <dt className="text-text-muted">{label}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}
