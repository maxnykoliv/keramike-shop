"use client";

import type { Layout } from "@/calc";
import { cn } from "@/shared/lib/cn";
import { Icon, NumberSlider, RadioCards } from "@/shared/ui";

import { LAYOUTS, newKey, type Opening, type SurfaceForm } from "../model";
import { TilePicker } from "./TilePicker";

type Props = {
  surface: SurfaceForm;
  index: number;
  canRemove: boolean;
  onChange: (patch: Partial<SurfaceForm>) => void;
  onRemove: () => void;
  errorFor: (field: string) => string | null;
  priceOf: (id: number, fallback: number) => number;
  waste: Record<string, string> | undefined;
};

const WASTE_HINT = (waste: Record<string, string> | undefined, layout: Layout) =>
  waste?.[layout] ? `запас ${Math.round(Number(waste[layout]) * 100)}%` : undefined;

export function SurfaceEditor({ surface, index, canRemove, onChange, onRemove, errorFor, priceOf, waste }: Props) {
  const path = `surfaces[${index}]`;
  const title = surface.kind === "floor" ? "Підлога" : "Стіни";
  const setOpening = (key: string, patch: Partial<Opening>) =>
    onChange({ openings: surface.openings.map((o) => (o.key === key ? { ...o, ...patch } : o)) });

  return (
    <section aria-labelledby={`${surface.key}-title`} className="flex flex-col gap-6 border-t border-line pt-6" data-testid={`surface-${surface.kind}`}>
      <div className="flex items-center justify-between gap-4">
        <h3 id={`${surface.key}-title`} className="t-h3">{title}</h3>
        {canRemove ? (
          <button type="button" onClick={onRemove} className="t-small inline-flex items-center gap-1 text-text-muted hover:text-text">
            <Icon name="trash" size={16} /> Прибрати
          </button>
        ) : null}
      </div>

      <div className="flex gap-2" role="group" aria-label={`${title}: як задати площу`}>
        {(["dims", "area"] as const).map((mode) => (
          <button key={mode} type="button" aria-pressed={surface.mode === mode} onClick={() => onChange({ mode })}
            className={cn("t-small min-h-10 rounded-[2px] border px-3",
              surface.mode === mode ? "border-text bg-surface/50" : "border-line text-text-muted")}>
            {mode === "dims" ? "Розміри приміщення" : "Знаю площу"}
          </button>
        ))}
      </div>

      {surface.mode === "dims" ? (
        <div className="flex flex-col gap-5">
          <NumberSlider label="Довжина, м" unit="м" min={0.1} max={20} step={0.05} value={surface.length}
            onChange={(length) => onChange({ length })} error={errorFor(`${path}.length_m`)} />
          <NumberSlider label="Ширина, м" unit="м" min={0.1} max={20} step={0.05} value={surface.width}
            onChange={(width) => onChange({ width })} error={errorFor(`${path}.width_m`)} />
          {surface.kind === "walls" ? (
            <NumberSlider label="Висота облицювання, м" unit="м" min={0.1} max={5} step={0.05} value={surface.height}
              onChange={(height) => onChange({ height })} error={errorFor(`${path}.height_m`)} />
          ) : null}
        </div>
      ) : (
        <NumberSlider label={`Площа ${surface.kind === "floor" ? "підлоги" : "стін"}, м²`} unit="м²" min={0.5} max={200} step={0.5}
          value={surface.area} onChange={(area) => onChange({ area })} error={errorFor(`${path}.area_m2`)} />
      )}

      {surface.kind === "walls" && surface.mode === "dims" ? (
        <fieldset className="flex flex-col gap-3">
          <legend className="t-small mb-2 font-medium">Двері й вікна</legend>
          {surface.openings.map((o, i) => (
            <div key={o.key} className="flex flex-wrap items-end gap-3" data-testid="opening">
              <label className="flex flex-col gap-1">
                <span className="t-small text-text-muted">Ширина, м</span>
                <input inputMode="decimal" value={o.width.replace(".", ",")} aria-label={`Проріз ${i + 1}: ширина`}
                  onChange={(e) => setOpening(o.key, { width: e.target.value.replace(",", ".") })}
                  className="tabular min-h-11 w-24 border-b border-line-strong bg-transparent focus:outline-none" />
              </label>
              <label className="flex flex-col gap-1">
                <span className="t-small text-text-muted">Висота, м</span>
                <input inputMode="decimal" value={o.height.replace(".", ",")} aria-label={`Проріз ${i + 1}: висота`}
                  onChange={(e) => setOpening(o.key, { height: e.target.value.replace(",", ".") })}
                  className="tabular min-h-11 w-24 border-b border-line-strong bg-transparent focus:outline-none" />
              </label>
              <label className="flex flex-col gap-1">
                <span className="t-small text-text-muted">Кількість</span>
                <input inputMode="numeric" value={o.count} aria-label={`Проріз ${i + 1}: кількість`}
                  onChange={(e) => setOpening(o.key, { count: Math.max(1, Math.min(20, Number(e.target.value.replace(/\D/g, "")) || 1)) })}
                  className="tabular min-h-11 w-16 border-b border-line-strong bg-transparent focus:outline-none" />
              </label>
              <button type="button" className="grid size-11 place-items-center text-text-muted hover:text-text"
                aria-label={`Прибрати проріз ${i + 1}`}
                onClick={() => onChange({ openings: surface.openings.filter((x) => x.key !== o.key) })}>
                <Icon name="close" size={16} />
              </button>
            </div>
          ))}
          <div className="flex flex-wrap gap-4">
            <button type="button" className="link t-small inline-flex items-center gap-1"
              onClick={() => onChange({ openings: [...surface.openings, { key: newKey(), width: "0.7", height: "2", count: 1 }] })}>
              <Icon name="door" size={16} /> Додати двері 0,7 × 2,0 м
            </button>
            <button type="button" className="link t-small inline-flex items-center gap-1"
              onClick={() => onChange({ openings: [...surface.openings, { key: newKey(), width: "1.2", height: "1.4", count: 1 }] })}>
              <Icon name="plus" size={16} /> Додати вікно
            </button>
          </div>
          {errorFor(`${path}.openings`) ? <p role="alert" className="t-small text-error">{errorFor(`${path}.openings`)}</p> : null}
        </fieldset>
      ) : null}

      <TilePicker tile={surface.tile} onChange={(tile) => onChange({ tile })} priceOf={priceOf} idPrefix={surface.key}
        error={errorFor(`${path}.tile`) ?? errorFor(`${path}.product_id`)} />

      <RadioCards legend="Спосіб укладання" name={`${surface.key}-layout`} value={surface.layout} columns={4}
        onChange={(layout) => onChange({ layout })}
        options={LAYOUTS.map((l) => ({ value: l.value, label: l.label, description: WASTE_HINT(waste, l.value) }))} />

      <NumberSlider label="Ширина шва, мм" unit="мм" min={0.5} max={10} step={0.5} value={surface.joint}
        onChange={(joint) => onChange({ joint })} />
    </section>
  );
}
