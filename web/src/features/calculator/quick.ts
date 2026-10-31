import { calculate, type CalcSettings, type Layout } from "@/calc";
import type { TileSpec } from "@/shared/api/types";

/** «Скільки мені потрібно?» на картці товару: лише плитка, без матеріалів і роботи. */
export function quickTileEstimate(spec: TileSpec, priceKop: number, area: string, layout: Layout, settings: CalcSettings) {
  const result = calculate({
    room: "other",
    surfaces: [{
      kind: spec.applications.includes("floor") ? "floor" : "walls",
      area_m2: area,
      layout,
      tile: {
        width_mm: spec.width_mm, height_mm: spec.height_mm, thickness_mm: spec.thickness_mm,
        price_kop_per_m2: priceKop, m2_per_pack: spec.m2_per_pack, pack_weight_kg: spec.pack_weight_kg,
      },
    }],
    include: { glue: false, grout: false, primer: false, waterproofing: false, labor: false },
  }, settings);
  const surface = result.surfaces[0]!;
  const line = result.lines[0]!;
  return { packs: surface.packs, areaWithWaste: surface.area_with_waste_m2, boughtM2: line.quantity_base, totalKop: line.total_kop };
}
