"use client";

import type { CalcResult } from "@/calc";
import { formatUah } from "@/shared/lib/money";
import { formatArea, formatDecimal, unitLabel } from "@/shared/lib/numbers";
import { Notice, Skeleton } from "@/shared/ui";

import type { Calculation } from "../hooks/useCalculation";
import type { CalcForm } from "../model";

const KIND_NAMES: Record<string, string> = {
  glue: "Клей", grout: "Затирка", primer: "Ґрунтовка", waterproofing: "Гідроізоляція", labor: "Робота майстра",
};

function Row({ title, detail, value, testId }: { title: string; detail?: string; value: string; testId?: string }) {
  return (
    <div className="flex items-baseline justify-between gap-4 bg-surface px-4 py-3" data-testid={testId}>
      <div>
        <p>{title}</p>
        {detail ? <p className="t-small text-text-muted tabular">{detail}</p> : null}
      </div>
      <p className="tabular shrink-0 font-semibold">{value}</p>
    </div>
  );
}

export function ResultPanel({ calculation, form }: { calculation: Calculation; form: CalcForm }) {
  if (calculation.state === "loading") {
    return <div className="flex flex-col gap-2"><Skeleton className="h-14" /><Skeleton className="h-14" /><Skeleton className="h-20" /></div>;
  }
  if (calculation.state === "invalid") {
    return <Notice tone="info">{calculation.message}</Notice>;
  }
  const result: CalcResult = calculation.result;
  return (
    <div className="flex flex-col gap-2" data-testid="calc-result">
      {result.surfaces.map((s, i) => (
        <Row key={`s${i}`} title={s.kind === "floor" ? "Площа підлоги" : "Площа стін"}
          detail={`із запасом ${formatArea(s.area_with_waste_m2)}`} value={formatArea(s.area_m2)} testId={`area-${s.kind}`} />
      ))}
      {result.lines.map((line, i) => {
        const surface = line.surface_index != null ? form.surfaces[line.surface_index] : null;
        const title = line.kind === "tile"
          ? `${line.name}${surface && form.surfaces.length > 1 ? `, ${surface.kind === "floor" ? "підлога" : "стіни"}` : ""}`
          : KIND_NAMES[line.kind] ?? line.name;
        const detail = line.kind === "labor"
          ? formatArea(line.quantity_base)
          : `${line.quantity} ${unitLabel(line.unit)} · ${formatDecimal(line.quantity_base)} ${unitLabel(line.base_unit)}`;
        return <Row key={`l${i}`} title={title} detail={detail} value={formatUah(line.total_kop)} testId={`line-${line.kind}`} />;
      })}
      {result.warnings.map((w, i) => <Notice key={`w${i}`} className="my-2">{w.message}</Notice>)}
      <div className="mt-2 flex items-baseline justify-between gap-4 border-t-2 border-accent bg-surface px-4 py-4" data-testid="calc-total">
        <div>
          <p className="font-semibold">Разом</p>
          <p className="t-small text-text-muted tabular">вага {formatDecimal(Number(result.weight_kg).toFixed(1))} кг</p>
        </div>
        <p className="t-price">{formatUah(result.total_kop)}</p>
      </div>
      <details className="t-small mt-2 text-text-muted">
        <summary className="cursor-pointer py-2">Як ми рахуємо</summary>
        <ul className="mt-2 flex list-disc flex-col gap-1 pl-5">
          <li>Площа стін = периметр × висота − двері й вікна.</li>
          <li>Упаковки = площа × (1 + запас) ÷ м² в упаковці, округлення вгору.</li>
          <li>Затирка = (a + b) ÷ (a × b) × товщина × шов × 1,5 кг/м².</li>
          <li>Клей, ґрунтовка й гідроізоляція — за витратою на м², цілими упаковками.</li>
        </ul>
      </details>
    </div>
  );
}
