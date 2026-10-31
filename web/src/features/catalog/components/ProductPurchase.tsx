"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import type { Layout } from "@/calc";
import { QtyStepper, useCartActions } from "@/features/cart";
import { LAYOUTS, quickTileEstimate, useCalcConfig } from "@/features/calculator";
import { friendlyMessage } from "@/shared/api/errors";
import type { ProductDetail, TileSpec } from "@/shared/api/types";
import { formatUah } from "@/shared/lib/money";
import { formatArea, formatDecimal, parseDecimal } from "@/shared/lib/numbers";
import { Button, Field, Icon, Notice, Price, Select, TextInput } from "@/shared/ui";

import { usePersonalPrices } from "../hooks/usePersonalPrices";

const STOCK: Record<string, string> = { in_stock: "В наявності", on_order: "Під замовлення", out_of_stock: "Немає в наявності" };

/** Price, the "how much do I need?" helper, quantity and the add-to-cart button. */
export function ProductPurchase({ product }: { product: ProductDetail }) {
  const tile = product.tile_spec as unknown as TileSpec | null;
  const { isMaster, priceOf } = usePersonalPrices([product.id]);
  const price = isMaster ? priceOf(product.id, product.price_kop) : product.price_kop;
  const config = useCalcConfig();
  const { add } = useCartActions();
  const [area, setArea] = useState("");
  const [layout, setLayout] = useState<Layout>("straight");
  const [qty, setQty] = useState(1);
  const [added, setAdded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const estimate = useMemo(() => {
    const value = parseDecimal(area);
    if (!tile || !config.data || !value || Number(value) <= 0 || Number(value) > 1000) return null;
    return quickTileEstimate(tile, price, value, layout, config.data);
  }, [area, layout, tile, config.data, price]);

  const packPrice = tile ? Math.round(Number(tile.m2_per_pack) * price) : price;

  const addToCart = async (count: number) => {
    setError(null);
    setAdded(false);
    try {
      await add.mutateAsync({ product_id: product.id, qty: count });
      setAdded(true);
    } catch (e) {
      setError(friendlyMessage(e));
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1">
        <Price kop={price} retailKop={isMaster ? product.price_kop : null} unit={product.unit} size="lg" />
        {tile ? <p className="t-small text-text-muted tabular">{formatUah(packPrice)} за упаковку · {formatArea(tile.m2_per_pack)}</p> : null}
        <p className="t-small" data-testid="stock">{STOCK[product.stock_status ?? "in_stock"] ?? ""}</p>
      </div>

      {tile ? (
        <section aria-labelledby="need-title" className="flex flex-col gap-4 bg-surface p-5">
          <h2 id="need-title" className="t-h3">Скільки мені потрібно?</h2>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Площа, м²">
              {(ids) => <TextInput ids={ids} inputMode="decimal" placeholder="Напр. 3,4" value={area}
                onChange={(e) => setArea(e.target.value)} data-testid="need-area" />}
            </Field>
            <Field label="Укладання">
              {(ids) => (
                <Select ids={ids} value={layout} onChange={(e) => setLayout(e.target.value as Layout)}>
                  {LAYOUTS.map((l) => <option key={l.value} value={l.value}>{l.label}</option>)}
                </Select>
              )}
            </Field>
          </div>
          {estimate ? (
            <div className="flex flex-col gap-3" data-testid="need-result" aria-live="polite">
              <p>
                <span className="font-semibold tabular">{estimate.packs} уп.</span>
                <span className="text-text-muted"> · {formatArea(estimate.boughtM2)} із запасом · </span>
                <span className="font-semibold tabular">{formatUah(estimate.totalKop)}</span>
              </p>
              <Button variant="secondary" onClick={() => { setQty(estimate.packs); addToCart(estimate.packs); }} loading={add.isPending}>
                Додати {estimate.packs} уп. у кошик
              </Button>
            </div>
          ) : (
            <p className="t-small text-text-muted">Запас на підрізку врахуємо за способом укладання.</p>
          )}
          <Link href={`/calculator?product=${product.slug}`} className="link t-small inline-flex items-center gap-1">
            <Icon name="calculator" size={16} /> Повний розрахунок ремонту з клеєм і роботою
          </Link>
        </section>
      ) : null}

      <div className="flex flex-wrap items-center gap-3">
        <QtyStepper label={tile ? "Кількість упаковок" : "Кількість"} value={qty} onChange={setQty} />
        {tile ? <span className="t-small text-text-muted">= {formatDecimal((qty * Number(tile.m2_per_pack)).toFixed(2))} м²</span> : null}
        <Button onClick={() => addToCart(qty)} loading={add.isPending} disabled={product.stock_status === "out_of_stock"}
          className="flex-1 md:flex-none">
          Додати в кошик
        </Button>
      </div>
      {added ? (
        <Notice tone="success">Додано в кошик. <Link href="/cart" className="link">Перейти до кошика</Link></Notice>
      ) : null}
      {error ? <Notice tone="error">{error}</Notice> : null}
    </div>
  );
}
