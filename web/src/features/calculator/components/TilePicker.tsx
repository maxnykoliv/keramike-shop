"use client";

import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { bff } from "@/shared/api/client";
import type { PaginatedProducts, ProductCard, ProductDetail } from "@/shared/api/types";
import { formatUnitPrice } from "@/shared/lib/money";
import { formatDecimal } from "@/shared/lib/numbers";
import { Field, Notice, Price, ProductVisual, Spinner, TextInput } from "@/shared/ui";

import { catalogTile, type CatalogTile, type ManualTile, type SurfaceForm } from "../model";

function useDebounced<T>(value: T, ms = 300) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), ms);
    return () => clearTimeout(timer);
  }, [value, ms]);
  return debounced;
}

export function TilePicker({
  tile, onChange, error, priceOf, idPrefix,
}: {
  tile: SurfaceForm["tile"];
  onChange: (tile: SurfaceForm["tile"]) => void;
  error?: string | null;
  priceOf: (id: number, fallback: number) => number;
  idPrefix: string;
}) {
  const [picking, setPicking] = useState(!tile);
  const [query, setQuery] = useState("");
  const [choosing, setChoosing] = useState<string | null>(null);
  const q = useDebounced(query.trim());
  const results = useQuery({
    queryKey: ["tile-search", q],
    queryFn: async () => q.length >= 2
      ? bff<ProductCard[]>(`catalog/search?q=${encodeURIComponent(q)}`)
      : (await bff<PaginatedProducts>("catalog/products?kind=tile&page_size=6")).results,
    enabled: picking,
    staleTime: 60_000,
  });

  const choose = async (product: ProductCard) => {
    setChoosing(product.slug);
    try {
      const detail = await bff<ProductDetail>(`catalog/products/${product.slug}`);
      const chosen = catalogTile(detail);
      if (chosen) {
        onChange(chosen);
        setPicking(false);
        setQuery("");
      }
    } finally {
      setChoosing(null);
    }
  };

  if (tile && !picking) {
    return (
      <div className="flex flex-col gap-2">
        <span className="t-small font-medium">Плитка</span>
        {tile.source === "catalog" ? <ChosenTile tile={tile} priceKop={priceOf(tile.productId, tile.priceKop)} /> : (
          <ManualFields tile={tile} onChange={onChange} idPrefix={idPrefix} />
        )}
        <div className="flex flex-wrap gap-4">
          <button type="button" className="link t-small" onClick={() => setPicking(true)}>
            {tile.source === "catalog" ? "Змінити плитку" : "Обрати з каталогу"}
          </button>
          {tile.source === "catalog" ? (
            <button type="button" className="link t-small" onClick={() => onChange(emptyManual())}>Вказати вручну</button>
          ) : null}
        </div>
        {error ? <p role="alert" className="t-small text-error">{error}</p> : null}
      </div>
    );
  }

  const items = results.data ?? [];
  return (
    <div className="flex flex-col gap-3">
      <Field label="Плитка: пошук у каталозі" error={error}>
        {(ids) => <TextInput ids={ids} type="search" placeholder="Назва або артикул" value={query}
          onChange={(e) => setQuery(e.target.value)} data-testid="tile-search" />}
      </Field>
      {results.isFetching ? <Spinner label="Шукаємо плитку" /> : null}
      <ul className="grid grid-cols-2 gap-3 md:grid-cols-3" aria-label="Знайдена плитка">
        {items.filter((p) => p.size).map((p) => (
          <li key={p.id}>
            <button type="button" onClick={() => choose(p)} disabled={choosing !== null} data-testid="tile-option"
              className="flex w-full flex-col gap-2 text-left disabled:opacity-60" aria-label={`Обрати ${p.name}`}>
              <ProductVisual image={p.image} name={p.name} size={p.size} sizes="160px" />
              <span className="t-small font-medium">{p.name}</span>
              <span className="t-small text-text-muted tabular">{formatUnitPrice(priceOf(p.id, p.price_kop), p.unit)}</span>
            </button>
          </li>
        ))}
      </ul>
      {!results.isFetching && q.length >= 2 && items.length === 0 ? <Notice tone="info">Нічого не знайшли. Вкажіть плитку вручну.</Notice> : null}
      <div className="flex flex-wrap gap-4">
        <button type="button" className="link t-small" onClick={() => { onChange(emptyManual()); setPicking(false); }}>
          Вказати плитку вручну
        </button>
        {tile ? <button type="button" className="link t-small" onClick={() => setPicking(false)}>Скасувати</button> : null}
      </div>
    </div>
  );
}

const emptyManual = (): ManualTile => ({ source: "manual", widthMm: "600", heightMm: "600", priceUah: "", m2PerPack: "1.44", packWeightKg: "" });

function ChosenTile({ tile, priceKop }: { tile: CatalogTile; priceKop: number }) {
  return (
    <div className="flex items-center gap-4 border border-line p-3" data-testid="chosen-tile">
      <div className="w-16 shrink-0"><ProductVisual image={tile.image} name={tile.name}
        size={`${tile.spec.width_mm}x${tile.spec.height_mm}`} color={tile.color} sizes="64px" /></div>
      <div className="flex flex-col">
        <span className="font-medium">{tile.name}</span>
        <span className="t-small text-text-muted">{tile.spec.width_mm} × {tile.spec.height_mm} мм · {formatDecimal(tile.spec.m2_per_pack)} м² в упаковці</span>
        <Price kop={priceKop} retailKop={priceKop !== tile.priceKop ? tile.priceKop : null} unit="m2" />
      </div>
    </div>
  );
}

function ManualFields({ tile, onChange, idPrefix }: { tile: ManualTile; onChange: (t: ManualTile) => void; idPrefix: string }) {
  const set = (patch: Partial<ManualTile>) => onChange({ ...tile, ...patch });
  return (
    <div className="grid grid-cols-2 gap-4 border border-line p-4" data-testid="manual-tile">
      <Field label="Ширина, мм" id={`${idPrefix}-w`}>{(ids) => <TextInput ids={ids} inputMode="numeric" value={tile.widthMm} onChange={(e) => set({ widthMm: e.target.value })} />}</Field>
      <Field label="Довжина, мм" id={`${idPrefix}-h`}>{(ids) => <TextInput ids={ids} inputMode="numeric" value={tile.heightMm} onChange={(e) => set({ heightMm: e.target.value })} />}</Field>
      <Field label="Ціна за м², грн" id={`${idPrefix}-p`}>{(ids) => <TextInput ids={ids} inputMode="decimal" value={tile.priceUah} onChange={(e) => set({ priceUah: e.target.value })} />}</Field>
      <Field label="М² в упаковці" id={`${idPrefix}-m`}>{(ids) => <TextInput ids={ids} inputMode="decimal" value={tile.m2PerPack} onChange={(e) => set({ m2PerPack: e.target.value })} />}</Field>
      <Field label="Вага упаковки, кг" hint="Необов'язково" className="col-span-2" id={`${idPrefix}-kg`}>
        {(ids) => <TextInput ids={ids} inputMode="decimal" value={tile.packWeightKg} onChange={(e) => set({ packWeightKg: e.target.value })} />}
      </Field>
    </div>
  );
}
