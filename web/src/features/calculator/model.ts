/** Calculator form model and conversion to engine input and to the server request. */
import type { CalcInput, Layout, Room, SurfaceKind, TileInput } from "@/calc";
import type { ProductDetail, TileSpec } from "@/shared/api/types";
import { tileSpecOf } from "@/shared/api/types";
import { parseDecimal } from "@/shared/lib/numbers";

export type IncludeKey = "glue" | "grout" | "primer" | "waterproofing" | "labor";

export type CatalogTile = {
  source: "catalog";
  productId: number;
  slug: string;
  name: string;
  priceKop: number;
  image: string | null;
  color: string;
  spec: TileSpec;
};

export type ManualTile = {
  source: "manual";
  widthMm: string;
  heightMm: string;
  priceUah: string;
  m2PerPack: string;
  packWeightKg: string;
};

export type Opening = { key: string; width: string; height: string; count: number };

export type SurfaceForm = {
  key: string;
  kind: SurfaceKind;
  mode: "dims" | "area";
  length: string;
  width: string;
  height: string;
  area: string;
  openings: Opening[];
  tile: CatalogTile | ManualTile | null;
  layout: Layout;
  joint: string;
};

export type CalcForm = {
  room: Room;
  surfaces: SurfaceForm[];
  include: Record<IncludeKey, boolean>;
};

let counter = 0;
export const newKey = () => `k${Date.now().toString(36)}${(counter++).toString(36)}`;

export const ROOMS: { value: Room; label: string }[] = [
  { value: "bathroom", label: "Ванна" },
  { value: "toilet", label: "Туалет" },
  { value: "kitchen", label: "Кухня" },
  { value: "hallway", label: "Коридор" },
  { value: "terrace", label: "Тераса" },
  { value: "other", label: "Інше" },
];

export const LAYOUTS: { value: Layout; label: string }[] = [
  { value: "straight", label: "Прямий" },
  { value: "offset", label: "Зі зміщенням" },
  { value: "diagonal", label: "Діагональ" },
  { value: "herringbone", label: "Ялинка" },
];

export const INCLUDES: { key: IncludeKey; label: string }[] = [
  { key: "glue", label: "Клей" },
  { key: "grout", label: "Затирка" },
  { key: "primer", label: "Ґрунтовка" },
  { key: "waterproofing", label: "Гідроізоляція" },
  { key: "labor", label: "Робота майстра" },
];

export function newSurface(kind: SurfaceKind, tile: SurfaceForm["tile"] = null): SurfaceForm {
  return {
    key: newKey(), kind, mode: "dims", length: kind === "floor" ? "2" : "2", width: "1.7",
    height: kind === "walls" ? "2.5" : "", area: "", openings: kind === "walls"
      ? [{ key: newKey(), width: "0.7", height: "2", count: 1 }] : [],
    tile, layout: "straight", joint: "2",
  };
}

export function defaultForm(): CalcForm {
  return {
    room: "bathroom",
    surfaces: [newSurface("floor")],
    include: { glue: true, grout: true, primer: true, waterproofing: true, labor: true },
  };
}

export function catalogTile(product: ProductDetail): CatalogTile | null {
  const spec = tileSpecOf(product);
  if (!spec) return null;
  return {
    source: "catalog", productId: product.id, slug: product.slug, name: product.name,
    priceKop: product.price_kop, image: product.image ?? null, color: spec.color, spec,
  };
}

export type BuildResult = { input: CalcInput } | { error: { field: string; message: string } };

/** Input for the in-browser engine. priceOf supplies the master price. */
export function toEngineInput(form: CalcForm, priceOf: (id: number, fallback: number) => number = (_, f) => f): BuildResult {
  const surfaces = [];
  for (const [index, surface] of form.surfaces.entries()) {
    const path = `surfaces[${index}]`;
    const tile = tileInput(surface.tile, priceOf);
    if ("error" in tile) return { error: { field: `${path}.tile`, message: tile.error } };
    surfaces.push({
      kind: surface.kind,
      tile: tile.tile,
      layout: surface.layout,
      joint_mm: parseDecimal(surface.joint) ?? "2",
      ...(surface.mode === "area"
        ? { area_m2: parseDecimal(surface.area) ?? undefined }
        : {
            length_m: parseDecimal(surface.length) ?? undefined,
            width_m: parseDecimal(surface.width) ?? undefined,
            height_m: surface.kind === "walls" ? parseDecimal(surface.height) ?? undefined : undefined,
          }),
      openings: surface.kind === "walls" && surface.mode === "dims"
        ? surface.openings.flatMap((o) => {
            const w = parseDecimal(o.width);
            const h = parseDecimal(o.height);
            return w && h ? [{ width_m: w, height_m: h, count: o.count }] : [];
          })
        : [],
    });
  }
  return { input: { room: form.room, surfaces, include: form.include } };
}

function tileInput(tile: SurfaceForm["tile"], priceOf: (id: number, fallback: number) => number):
  { tile: TileInput } | { error: string } {
  if (!tile) return { error: "Оберіть плитку з каталогу або вкажіть її вручну" };
  if (tile.source === "catalog") {
    return {
      tile: {
        width_mm: tile.spec.width_mm, height_mm: tile.spec.height_mm, thickness_mm: tile.spec.thickness_mm,
        price_kop_per_m2: priceOf(tile.productId, tile.priceKop), m2_per_pack: tile.spec.m2_per_pack,
        pack_weight_kg: tile.spec.pack_weight_kg, product_id: tile.productId, name: tile.name,
        applications: tile.spec.applications,
      },
    };
  }
  const width = Number(parseDecimal(tile.widthMm));
  const height = Number(parseDecimal(tile.heightMm));
  const price = parseDecimal(tile.priceUah);
  const m2 = parseDecimal(tile.m2PerPack);
  if (!width || !height || width < 10 || height < 10) return { error: "Вкажіть розмір плитки в міліметрах" };
  if (price === null) return { error: "Вкажіть ціну за м²" };
  if (!m2 || Number(m2) <= 0) return { error: "Вкажіть, скільки м² в упаковці" };
  return {
    tile: {
      width_mm: Math.round(width), height_mm: Math.round(height),
      price_kop_per_m2: Math.round(Number(price) * 100), m2_per_pack: m2,
      pack_weight_kg: parseDecimal(tile.packWeightKg) ?? null, name: `Плитка ${Math.round(width)}×${Math.round(height)}`,
    },
  };
}

/** Server request body: catalog tiles go as product_id, and the backend looks up prices itself. */
export function toServerPayload(form: CalcForm) {
  return {
    room: form.room,
    include: form.include,
    surfaces: form.surfaces.map((s) => ({
      kind: s.kind,
      layout: s.layout,
      joint_mm: parseDecimal(s.joint) ?? "2",
      ...(s.tile?.source === "catalog"
        ? { product_id: s.tile.productId }
        : s.tile
          ? {
              tile: {
                width_mm: Math.round(Number(parseDecimal(s.tile.widthMm))),
                height_mm: Math.round(Number(parseDecimal(s.tile.heightMm))),
                price_kop_per_m2: Math.round(Number(parseDecimal(s.tile.priceUah)) * 100),
                m2_per_pack: parseDecimal(s.tile.m2PerPack),
                ...(parseDecimal(s.tile.packWeightKg) ? { pack_weight_kg: parseDecimal(s.tile.packWeightKg) } : {}),
              },
            }
          : {}),
      ...(s.mode === "area"
        ? { area_m2: parseDecimal(s.area) }
        : {
            length_m: parseDecimal(s.length),
            width_m: parseDecimal(s.width),
            ...(s.kind === "walls" ? { height_m: parseDecimal(s.height) } : {}),
          }),
      openings: s.kind === "walls" && s.mode === "dims"
        ? s.openings.filter((o) => parseDecimal(o.width) && parseDecimal(o.height))
            .map((o) => ({ width_m: parseDecimal(o.width), height_m: parseDecimal(o.height), count: o.count }))
        : [],
    })),
  };
}

type ServerSurface = {
  kind: SurfaceKind; layout?: Layout; joint_mm?: string; product_id?: number;
  tile?: { width_mm: number; height_mm: number; price_kop_per_m2: number; m2_per_pack?: string; pack_weight_kg?: string };
  length_m?: string; width_m?: string; height_m?: string; area_m2?: string;
  openings?: { width_m: string; height_m: string; count?: number }[];
};

/** Saved estimate → form. loadTiles fills in the catalog tiles. */
export function formFromServerInput(
  input: { room?: Room; include?: Partial<Record<IncludeKey, boolean>>; surfaces: ServerSurface[] },
  tiles: Map<number, CatalogTile>,
): CalcForm {
  const base = defaultForm();
  return {
    room: input.room ?? "other",
    include: { ...base.include, ...input.include },
    surfaces: input.surfaces.map((s) => ({
      key: newKey(),
      kind: s.kind,
      mode: s.area_m2 ? "area" : "dims",
      length: s.length_m ?? "",
      width: s.width_m ?? "",
      height: s.height_m ?? "",
      area: s.area_m2 ?? "",
      openings: (s.openings ?? []).map((o) => ({ key: newKey(), width: o.width_m, height: o.height_m, count: o.count ?? 1 })),
      layout: s.layout ?? "straight",
      joint: s.joint_mm ?? "2",
      tile: s.product_id
        ? tiles.get(s.product_id) ?? null
        : s.tile
          ? {
              source: "manual", widthMm: String(s.tile.width_mm), heightMm: String(s.tile.height_mm),
              priceUah: String(s.tile.price_kop_per_m2 / 100), m2PerPack: s.tile.m2_per_pack ?? "",
              packWeightKg: s.tile.pack_weight_kg ?? "",
            }
          : null,
    })),
  };
}

/** Form fingerprint: if it has not changed, the saved estimate is reused. */
export const formFingerprint = (form: CalcForm) => JSON.stringify(toServerPayload(form));
