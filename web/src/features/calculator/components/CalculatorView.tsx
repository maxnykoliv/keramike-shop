"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { usePersonalPricesForTiles } from "../hooks/usePersonalPricesForTiles";
import { useCalcConfig } from "../hooks/useCalcConfig";
import { useCalculation } from "../hooks/useCalculation";
import { bff } from "@/shared/api/client";
import type { EstimateDetail, PaginatedProducts, ProductDetail } from "@/shared/api/types";
import { track } from "@/shared/lib/analytics";
import { formatUah } from "@/shared/lib/money";
import { readJson, writeJson } from "@/shared/lib/storage";
import { Checkbox, Icon, Notice, RadioCards, Skeleton } from "@/shared/ui";

import {
  ROOMS, INCLUDES, catalogTile, defaultForm, formFromServerInput, newSurface,
  type CalcForm, type CatalogTile, type SurfaceForm,
} from "../model";
import { ResultActions } from "./ResultActions";
import { ResultPanel } from "./ResultPanel";
import { SurfaceEditor } from "./SurfaceEditor";

const DRAFT_KEY = "kr_calc_draft_v1";

const STEPS = [
  "Заміряйте приміщення: довжину, ширину й висоту облицювання.",
  "Вкажіть розміри або готову площу, додайте двері й вікна.",
  "Оберіть плитку з каталогу або вкажіть її вручну.",
  "Перевірте результат праворуч: упаковки, матеріали, робота.",
  "Додайте все в кошик або надішліть розрахунок менеджеру.",
];

async function loadTiles(ids: number[]): Promise<Map<number, CatalogTile>> {
  const map = new Map<number, CatalogTile>();
  if (ids.length === 0) return map;
  const list = await bff<PaginatedProducts>(`catalog/products?ids=${ids.join(",")}&page_size=48`);
  const details = await Promise.all(list.results.map((p) => bff<ProductDetail>(`catalog/products/${p.slug}`)));
  for (const detail of details) {
    const tile = catalogTile(detail);
    if (tile) map.set(detail.id, tile);
  }
  return map;
}

export function CalculatorView({ productSlug, estimateCode }: { productSlug?: string; estimateCode?: string }) {
  const [form, setForm] = useState<CalcForm | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const started = useRef(false);
  const config = useCalcConfig();

  // Initial state: saved estimate → tile from the product card → draft → example.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        if (estimateCode) {
          const estimate = await bff<EstimateDetail>(`calc/estimates/${estimateCode}`);
          const input = estimate.input as Parameters<typeof formFromServerInput>[0];
          const ids = input.surfaces.flatMap((s) => (s.product_id ? [s.product_id] : []));
          const next = formFromServerInput(input, await loadTiles(ids));
          if (!cancelled) setForm(next);
          if (next.surfaces.some((s) => !s.tile)) setNotice("Частини плитки вже немає в каталозі — оберіть заміну.");
          return;
        }
        if (productSlug) {
          const detail = await bff<ProductDetail>(`catalog/products/${productSlug}`);
          const tile = catalogTile(detail);
          const base = readJson<CalcForm>(DRAFT_KEY) ?? defaultForm();
          const kind = tile?.spec.applications.includes("floor") ? "floor" : "walls";
          const surfaces = base.surfaces.length ? base.surfaces : [newSurface(kind)];
          if (!cancelled) setForm({ ...base, surfaces: surfaces.map((s, i) => (i === 0 ? { ...s, tile } : s)) });
          return;
        }
      } catch {
        if (!cancelled) setNotice("Не вдалося відкрити розрахунок, починаємо з нового.");
      }
      const draft = readJson<CalcForm>(DRAFT_KEY);
      if (draft) {
        // Prices and stock in the draft may be stale, so fetch fresh ones from the catalog.
        const ids = draft.surfaces.flatMap((s) => (s.tile?.source === "catalog" ? [s.tile.productId] : []));
        const fresh = await loadTiles(ids).catch(() => null);
        if (fresh) {
          draft.surfaces = draft.surfaces.map((s) => (
            s.tile?.source === "catalog" ? { ...s, tile: fresh.get(s.tile.productId) ?? null } : s
          ));
        }
      }
      if (!cancelled) setForm(draft ?? defaultForm());
    })();
    return () => { cancelled = true; };
  }, [estimateCode, productSlug]);

  // Draft in the browser: an accidentally closed tab does not lose the numbers.
  useEffect(() => {
    if (!form) return;
    const timer = setTimeout(() => writeJson(DRAFT_KEY, form), 400);
    return () => clearTimeout(timer);
  }, [form]);

  const { priceOf } = usePersonalPricesForTiles(form);
  const calculation = useCalculation(form ?? defaultForm(), form ? config.data : undefined, priceOf);

  useEffect(() => {
    if (calculation.state === "ready" && !started.current) {
      started.current = true;
      track("calculator_result", { room: form?.room ?? "other", total: calculation.result.total_kop / 100 });
    }
  }, [calculation, form?.room]);

  const errorFor = useMemo(() => {
    const field = calculation.state === "invalid" ? calculation.field : null;
    const message = calculation.state === "invalid" ? calculation.message : null;
    return (path: string) => (field === path ? message : null);
  }, [calculation]);

  if (!form || config.isLoading) {
    return <div className="grid gap-10 md:grid-cols-[1fr_400px]"><Skeleton className="h-[600px]" /><Skeleton className="h-80" /></div>;
  }
  if (config.isError) {
    return <Notice tone="error">Калькулятор тимчасово недоступний. Спробуйте оновити сторінку.</Notice>;
  }

  const update = (patch: Partial<CalcForm>) => setForm((f) => (f ? { ...f, ...patch } : f));
  const updateSurface = (key: string, patch: Partial<SurfaceForm>) =>
    setForm((f) => (f ? { ...f, surfaces: f.surfaces.map((s) => (s.key === key ? { ...s, ...patch } : s)) } : f));
  const hasKind = (kind: SurfaceForm["kind"]) => form.surfaces.some((s) => s.kind === kind);
  const addSurface = (kind: SurfaceForm["kind"]) => {
    const tile = form.surfaces.find((s) => s.tile)?.tile ?? null;
    update({ surfaces: [...form.surfaces, newSurface(kind, tile)] });
  };
  const total = calculation.state === "ready" ? calculation.result.total_kop : null;

  return (
    <div className="grid gap-12 pb-24 md:grid-cols-[1fr_400px] md:items-start md:gap-16 md:pb-0">
      <div className="flex flex-col gap-10">
        <details className="border-y border-line py-4" open>
          <summary className="t-label cursor-pointer text-accent-strong">Послідовність дій</summary>
          <ol className="mt-4 flex list-decimal flex-col gap-2 pl-5 text-text-muted">
            {STEPS.map((s) => <li key={s}>{s}</li>)}
          </ol>
        </details>
        {notice ? <Notice>{notice}</Notice> : null}

        <RadioCards legend="1. Приміщення" name="room" value={form.room} columns={3}
          onChange={(room) => update({ room })} options={ROOMS} />

        <div className="flex flex-col gap-6">
          <h2 className="t-small font-medium">2. Що облицьовуємо</h2>
          {form.surfaces.map((surface, index) => (
            <SurfaceEditor key={surface.key} surface={surface} index={index} canRemove={form.surfaces.length > 1}
              onChange={(patch) => updateSurface(surface.key, patch)}
              onRemove={() => update({ surfaces: form.surfaces.filter((s) => s.key !== surface.key) })}
              errorFor={errorFor} priceOf={priceOf} waste={config.data?.waste_by_layout} />
          ))}
          <div className="flex flex-wrap gap-3">
            {!hasKind("floor") ? <button type="button" className="link inline-flex items-center gap-1" onClick={() => addSurface("floor")}><Icon name="plus" size={16} />Додати підлогу</button> : null}
            {!hasKind("walls") ? <button type="button" className="link inline-flex items-center gap-1" onClick={() => addSurface("walls")}><Icon name="plus" size={16} />Додати стіни</button> : null}
          </div>
        </div>

        <fieldset className="flex flex-col">
          <legend className="t-small mb-2 font-medium">3. Додатково</legend>
          <div className="grid grid-cols-1 md:grid-cols-2">
            {INCLUDES.map((item) => (
              <Checkbox key={item.key} label={item.label} checked={form.include[item.key]}
                hint={item.key === "waterproofing" ? "Лише для ванної й туалету" : undefined}
                onChange={(e) => update({ include: { ...form.include, [item.key]: e.target.checked } })} />
            ))}
          </div>
        </fieldset>
      </div>

      <aside id="result" aria-labelledby="result-title" className="flex flex-col gap-6 md:sticky md:top-28">
        <h2 id="result-title" className="t-h2 text-accent-strong">Результат</h2>
        <ResultPanel calculation={calculation} form={form} />
        <ResultActions form={form} localTotal={total} disabled={calculation.state !== "ready"} />
      </aside>

      {/* Bottom bar on phones: the total is always visible. */}
      <div className="fixed inset-x-0 bottom-0 z-20 flex items-center justify-between gap-4 border-t border-line bg-bg px-4 py-3 md:hidden"
        data-testid="mobile-total">
        <div>
          <p className="t-small text-text-muted">Разом</p>
          <p className="t-price">{total !== null ? formatUah(total) : "—"}</p>
        </div>
        <a href="#result" className="t-label inline-flex min-h-11 items-center bg-button px-5 text-bg">Деталі</a>
      </div>
    </div>
  );
}
