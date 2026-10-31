// Порт рушія калькулятора з backend/apps/calc/engine/core.py.
// Лише для миттєвого показу в браузері: остаточну суму завжди рахує сервер.
// Збіг до копійки перевіряють спільні еталони calc-cases.

import DecimalBase from "decimal.js";
import type {
  CalcInput,
  CalcResult,
  CalcSettings,
  LineResult,
  MaterialKind,
  SizeClass,
  SurfaceInput,
  TileInput,
} from "./types";

// Як контекст decimal у Python: 28 значущих цифр, банківське округлення проміжних операцій.
const Decimal = DecimalBase.clone({ precision: 28, rounding: DecimalBase.ROUND_HALF_EVEN });
type D = InstanceType<typeof Decimal>;

const ZERO = new Decimal(0);
const MIN_SIDE = new Decimal("0.1");
const MAX_SIDE = new Decimal("50");
const MAX_HEIGHT = new Decimal("5");
const MAX_AREA = new Decimal("1000");
const WET_ROOMS = new Set(["bathroom", "toilet"]);

export class CalcValidationError extends Error {
  constructor(public code: string, message: string, public field: string) {
    super(message);
  }
}

const dec = (value: string | number | null | undefined): D | null =>
  value === null || value === undefined || value === "" ? null : new Decimal(value);

const round2 = (v: D): D => v.toDecimalPlaces(2, Decimal.ROUND_HALF_UP);
const ceilInt = (v: D): number => v.ceil().toNumber();
const kop = (v: D): number => v.toDecimalPlaces(0, Decimal.ROUND_HALF_UP).toNumber();
const fmt2 = (v: D): string => round2(v).toFixed(2);
const fmt3 = (v: D): string => v.toDecimalPlaces(3, Decimal.ROUND_HALF_UP).toFixed(3);

export function sizeClass(tile: TileInput): SizeClass {
  const side = Math.max(tile.width_mm, tile.height_mm);
  if (side <= 300) return "small";
  if (side <= 600) return "medium";
  return "large";
}

export function m2PerPack(tile: TileInput, path: string): D {
  const given = dec(tile.m2_per_pack);
  if (given && !given.isZero()) return given;
  if (tile.pcs_per_pack) {
    const area = new Decimal(tile.width_mm).times(tile.height_mm).div(1_000_000);
    return area.times(tile.pcs_per_pack).toDecimalPlaces(3, Decimal.ROUND_HALF_UP);
  }
  throw new CalcValidationError("pack_unknown", "Невідомо, скільки м² в упаковці", `${path}.tile`);
}

function checkSide(value: D | null, path: string, maximum: D = MAX_SIDE): D {
  if (value === null) throw new CalcValidationError("required", "Вкажіть розмір", path);
  if (value.lt(MIN_SIDE) || value.gt(maximum)) {
    throw new CalcValidationError(
      "out_of_range", `Розмір має бути від ${MIN_SIDE} до ${maximum} м`, path,
    );
  }
  return value;
}

export function surfaceArea(surface: SurfaceInput, path: string): D {
  const area = dec(surface.area_m2);
  if (area !== null) {
    if (area.lte(0) || area.gt(MAX_AREA)) {
      throw new CalcValidationError(
        "out_of_range", "Площа має бути від 0 до 1000 м²", `${path}.area_m2`,
      );
    }
    return round2(area);
  }
  const length = checkSide(dec(surface.length_m), `${path}.length_m`);
  const width = checkSide(dec(surface.width_m), `${path}.width_m`);
  if (surface.kind === "floor") return round2(length.times(width));

  const height = checkSide(dec(surface.height_m), `${path}.height_m`, MAX_HEIGHT);
  const gross = length.plus(width).times(2).times(height);
  const openings = (surface.openings ?? []).reduce(
    (sum, o) => sum.plus(new Decimal(o.width_m).times(o.height_m).times(o.count ?? 1)),
    ZERO,
  );
  if (openings.gte(gross)) {
    throw new CalcValidationError(
      "openings_exceed_area", "Прорізи не можуть бути більшими за площу стін",
      `${path}.openings`,
    );
  }
  return round2(gross.minus(openings));
}

export function groutKgPerM2(tile: TileInput, jointMm: D, density: D): D {
  const a = new Decimal(tile.width_mm);
  const b = new Decimal(tile.height_mm);
  return a.plus(b).div(a.times(b)).times(tile.thickness_mm ?? 8).times(jointMm).times(density);
}

export function calculate(data: CalcInput, settings: CalcSettings): CalcResult {
  if (!data.surfaces.length) {
    throw new CalcValidationError("required", "Додайте хоча б одну поверхню", "surfaces");
  }
  const room = data.room ?? "other";
  const include = { glue: true, grout: true, primer: true, waterproofing: true, labor: true,
                    ...(data.include ?? {}) };

  const surfaces: CalcResult["surfaces"] = [];
  const lines: LineResult[] = [];
  const warnings: CalcResult["warnings"] = [];
  let glueKg = ZERO;
  let groutKg = ZERO;
  let totalArea = ZERO;
  let laborKop = ZERO;

  data.surfaces.forEach((surface, index) => {
    const path = `surfaces[${index}]`;
    const tile = surface.tile;
    const layout = surface.layout ?? "straight";
    const area = surfaceArea(surface, path);
    const areaWithWaste = area.times(new Decimal(1).plus(settings.waste_by_layout[layout]));
    const perPack = m2PerPack(tile, path);
    const packs = ceilInt(areaWithWaste.div(perPack));
    const boughtM2 = perPack.times(packs);
    const cls = sizeClass(tile);

    surfaces.push({ kind: surface.kind, area_m2: fmt2(area),
                    area_with_waste_m2: fmt2(areaWithWaste), packs });
    lines.push({
      kind: "tile",
      name: tile.name ?? "Плитка",
      product_id: tile.product_id ?? null,
      quantity: String(packs),
      unit: "pack",
      quantity_base: fmt2(boughtM2),
      base_unit: "m2",
      total_kop: kop(boughtM2.times(tile.price_kop_per_m2)),
      weight_kg: fmt3((dec(tile.pack_weight_kg) ?? ZERO).times(packs)),
      surface_index: index,
    });

    const stock = dec(tile.stock_m2);
    if (stock !== null && boughtM2.gt(stock)) {
      warnings.push({ code: "insufficient_stock",
                      message: `На складі ${stock} м², потрібно ${fmt2(boughtM2)} м²`,
                      surface_index: index });
    }
    const applications = tile.applications ?? [];
    if (surface.kind === "floor" && applications.length && !applications.includes("floor")) {
      warnings.push({ code: "tile_not_for_floor", message: "Ця плитка не призначена для підлоги",
                      surface_index: index });
    }

    const joint = dec(surface.joint_mm) ?? new Decimal(2);
    glueKg = glueKg.plus(area.times(settings.glue_kg_per_m2[cls]));
    groutKg = groutKg.plus(area.times(groutKgPerM2(tile, joint, new Decimal(settings.grout_density))));
    laborKop = laborKop.plus(area.times(settings.labor_kop_per_m2[surface.kind][cls]));
    totalArea = totalArea.plus(area);
  });

  const wanted: [boolean, MaterialKind, D, string][] = [
    [include.glue, "glue", glueKg, "kg"],
    [include.grout, "grout", groutKg, "kg"],
    [include.primer, "primer", totalArea.times(settings.primer_l_per_m2), "l"],
    [include.waterproofing && WET_ROOMS.has(room), "waterproofing",
     totalArea.times(settings.waterproofing_kg_per_m2), "kg"],
  ];
  for (const [enabled, kind, amount, baseUnit] of wanted) {
    if (!enabled) continue;
    const product = settings.materials[kind];
    if (!product) {
      warnings.push({ code: "material_not_configured",
                      message: `Матеріал «${kind}» не налаштований`, surface_index: null });
      continue;
    }
    const packs = ceilInt(amount.div(product.pack_size));
    lines.push({
      kind,
      name: product.name,
      product_id: product.product_id ?? null,
      quantity: String(packs),
      unit: "pack",
      quantity_base: fmt2(amount),
      base_unit: baseUnit,
      total_kop: packs * product.price_kop,
      weight_kg: fmt3(new Decimal(product.pack_weight_kg ?? "0").times(packs)),
      surface_index: null,
    });
  }

  if (WET_ROOMS.has(room) && !include.waterproofing) {
    warnings.push({ code: "waterproofing_recommended",
                    message: "Для ванної й туалету рекомендуємо гідроізоляцію",
                    surface_index: null });
  }

  if (include.labor) {
    lines.push({
      kind: "labor", name: "Робота майстра", product_id: null,
      quantity: fmt2(totalArea), unit: "m2", quantity_base: fmt2(totalArea), base_unit: "m2",
      total_kop: kop(laborKop), weight_kg: "0.000", surface_index: null,
    });
  }

  const weight = lines.reduce((sum, line) => sum.plus(line.weight_kg), ZERO);
  return {
    settings_version: settings.version,
    surfaces,
    lines,
    total_kop: lines.reduce((sum, line) => sum + line.total_kop, 0),
    weight_kg: fmt3(weight),
    warnings,
  };
}
