import type { components } from "./schema";

type S = components["schemas"];

export type ProductCard = S["ProductCard"];
export type ProductDetail = S["ProductDetail"];
export type ProductImage = S["Image"];
export type PaginatedProducts = S["PaginatedProductCardList"];
export type Cart = S["Cart"];
export type CartLine = S["CartLine"];
export type CalcResult = S["CalcResult"];
export type CalcLine = S["LineResult"];
export type CalcWarning = S["Warning"];
export type EstimateCreated = S["EstimateCreated"];
export type EstimateDetail = S["EstimateDetail"];
export type PdfStatus = S["PdfStatus"];
export type CheckoutResult = S["CheckoutResult"];
export type PublicOrder = S["PublicOrder"];
export type OrderItem = S["OrderItem"];
export type Customer = S["Customer"];
export type Address = S["Address"];
export type AccountEstimate = S["AccountEstimate"];
export type City = S["City"];
export type Warehouse = S["Warehouse"];
export type AuthMethods = S["AuthMethods"];
export type TelegramPollResult = S["TelegramPollResult"];
export type PricesResponse = S["PricesResponse"];

/** tile_spec у ProductDetail описаний у схемі як довільний об'єкт — уточнюємо тут. */
export type TileSpec = {
  width_mm: number;
  height_mm: number;
  thickness_mm: number;
  m2_per_pack: string;
  pcs_per_pack: number | null;
  pack_weight_kg: string | null;
  material: string;
  surface: string;
  color: string;
  applications: string[];
  rooms: string[];
};

export type MaterialSpec = { pack_size: string; pack_unit: string; consumption_hint: string };

export type CategoryNode = { slug: string; name: string; children: CategoryNode[] };

export type Facets = {
  kinds: { kind: string; count: number }[];
  sizes: { size: string; count: number }[];
  colors: { color: string; count: number }[];
  surfaces: { surface: string; count: number }[];
  manufacturers: { slug: string; name: string; count: number }[];
  price_kop: { min: number | null; max: number | null };
};

export function tileSpecOf(product: ProductDetail): TileSpec | null {
  return (product.tile_spec as unknown as TileSpec | null) ?? null;
}

export type PaginatedOrders = S["PaginatedPublicOrderList"];
export type PaginatedEstimates = S["PaginatedAccountEstimateList"];
