// Формат вводу, налаштувань і результату — той самий, що в API та calc-cases.
// Десяткові числа — рядки, гроші — цілі копійки.

export type Room = "bathroom" | "toilet" | "kitchen" | "hallway" | "terrace" | "living" | "other";
export type SurfaceKind = "floor" | "walls";
export type Layout = "straight" | "offset" | "diagonal" | "herringbone";
export type SizeClass = "small" | "medium" | "large";
export type MaterialKind = "glue" | "grout" | "primer" | "waterproofing";

export interface TileInput {
  width_mm: number;
  height_mm: number;
  price_kop_per_m2: number;
  thickness_mm?: number;
  m2_per_pack?: string | null;
  pcs_per_pack?: number | null;
  pack_weight_kg?: string | null;
  product_id?: number | null;
  name?: string;
  stock_m2?: string | null;
  applications?: string[];
}

export interface OpeningInput {
  width_m: string;
  height_m: string;
  count?: number;
}

export interface SurfaceInput {
  kind: SurfaceKind;
  tile: TileInput;
  layout?: Layout;
  joint_mm?: string;
  length_m?: string;
  width_m?: string;
  height_m?: string;
  area_m2?: string;
  openings?: OpeningInput[];
}

export interface CalcInput {
  room?: Room;
  surfaces: SurfaceInput[];
  include?: Partial<Record<MaterialKind | "labor", boolean>>;
}

export interface MaterialProduct {
  name: string;
  pack_size: string;
  price_kop: number;
  pack_weight_kg?: string;
  product_id?: number | null;
}

export interface CalcSettings {
  version: number;
  waste_by_layout: Record<Layout, string>;
  glue_kg_per_m2: Record<SizeClass, string>;
  grout_density: string;
  primer_l_per_m2: string;
  waterproofing_kg_per_m2: string;
  labor_kop_per_m2: Record<SurfaceKind, Record<SizeClass, number>>;
  materials: Partial<Record<MaterialKind, MaterialProduct>>;
}

export interface LineResult {
  kind: string;
  name: string;
  product_id: number | null;
  quantity: string;
  unit: string;
  quantity_base: string;
  base_unit: string;
  total_kop: number;
  weight_kg: string;
  surface_index: number | null;
}

export interface CalcResult {
  settings_version: number;
  surfaces: { kind: SurfaceKind; area_m2: string; area_with_waste_m2: string; packs: number }[];
  lines: LineResult[];
  total_kop: number;
  weight_kg: string;
  warnings: { code: string; message: string; surface_index: number | null }[];
}
