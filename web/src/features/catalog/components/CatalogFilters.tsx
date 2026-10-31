"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useState, useTransition, type ReactNode } from "react";

import type { Facets } from "@/shared/api/types";
import { cn } from "@/shared/lib/cn";
import { Button, Dialog, Icon } from "@/shared/ui";

import { APPLICATION_LABELS, KIND_LABELS, ROOM_LABELS, SORT_OPTIONS } from "../labels";

type Option = { value: string; label: string; count?: number };

function useFilterUrl() {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const [pending, start] = useTransition();
  const set = (key: string, value: string | null) => {
    const next = new URLSearchParams(params);
    if (value === null || value === "" || next.get(key) === value) next.delete(key);
    else next.set(key, value);
    next.delete("page");
    start(() => router.push(`${pathname}${next.size ? `?${next}` : ""}`, { scroll: false }));
  };
  const clear = () => start(() => router.push(pathname, { scroll: false }));
  return { params, set, clear, pending };
}

function Group({ title, name, options, value, onPick }: {
  title: string; name: string; options: Option[]; value: string | null; onPick: (v: string) => void;
}) {
  if (options.length === 0) return null;
  return (
    <fieldset className="border-t border-line py-5">
      <legend className="t-label mb-3 text-text-muted">{title}</legend>
      <ul className="flex flex-col">
        {options.map((o) => (
          <li key={o.value}>
            <label className="flex min-h-10 cursor-pointer items-center justify-between gap-3">
              <span className="flex items-center gap-3">
                <input type="radio" name={name} checked={value === o.value} onChange={() => onPick(o.value)}
                  onClick={() => value === o.value && onPick(o.value)} className="size-4 accent-[var(--color-button)]" />
                {o.label}
              </span>
              {o.count != null ? <span className="t-small tabular text-text-muted">{o.count}</span> : null}
            </label>
          </li>
        ))}
      </ul>
    </fieldset>
  );
}

function Panel({ facets }: { facets: Facets }) {
  const { params, set } = useFilterUrl();
  const groups: { key: string; title: string; options: Option[] }[] = [
    { key: "room", title: "Приміщення", options: Object.entries(ROOM_LABELS).map(([value, label]) => ({ value, label })) },
    { key: "application", title: "Призначення", options: Object.entries(APPLICATION_LABELS).map(([value, label]) => ({ value, label })) },
    { key: "kind", title: "Тип", options: facets.kinds.map((k) => ({ value: k.kind, label: KIND_LABELS[k.kind] ?? k.kind, count: k.count })) },
    { key: "size", title: "Розмір, мм", options: facets.sizes.map((s) => ({ value: s.size, label: s.size.replace("x", " × "), count: s.count })) },
    { key: "color", title: "Колір", options: facets.colors.map((c) => ({ value: c.color, label: c.color, count: c.count })) },
    { key: "surface", title: "Поверхня", options: facets.surfaces.map((s) => ({ value: s.surface, label: s.surface, count: s.count })) },
    { key: "manufacturer", title: "Виробник", options: facets.manufacturers.map((m) => ({ value: m.slug, label: m.name, count: m.count })) },
  ];
  return (
    <div>
      {groups.map((g) => (
        <Group key={g.key} title={g.title} name={g.key} options={g.options} value={params.get(g.key)}
          onPick={(v) => set(g.key, v)} />
      ))}
      <div className="border-t border-line py-5">
        <label className="flex min-h-10 cursor-pointer items-center gap-3">
          <input type="checkbox" checked={params.get("in_stock") === "true"} className="size-4 accent-[var(--color-button)]"
            onChange={(e) => set("in_stock", e.target.checked ? "true" : null)} />
          Лише в наявності
        </label>
      </div>
    </div>
  );
}

export function CatalogFilters({ facets }: { facets: Facets }) {
  return (
    <aside aria-label="Фільтри" className="hidden md:block">
      <Panel facets={facets} />
    </aside>
  );
}

const CHIP_LABELS: Record<string, (v: string) => string> = {
  room: (v) => ROOM_LABELS[v] ?? v,
  application: (v) => APPLICATION_LABELS[v] ?? v,
  kind: (v) => KIND_LABELS[v] ?? v,
  size: (v) => v.replace("x", " × "),
  in_stock: () => "В наявності",
};

/** Рядок над сіткою: кнопка фільтрів (телефон), активні фільтри плашками, сортування. */
export function CatalogToolbar({ facets, count }: { facets: Facets; count: number }) {
  const { params, set, clear, pending } = useFilterUrl();
  const [open, setOpen] = useState(false);
  const chips = [...params.entries()].filter(([k]) => !["page", "ordering"].includes(k));
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="t-small text-text-muted" aria-live="polite" data-testid="result-count">
          {pending ? "Оновлюємо…" : `Знайдено: ${count}`}
        </p>
        <div className="flex items-center gap-3">
          <Button variant="secondary" size="sm" className="md:hidden" onClick={() => setOpen(true)}>
            <Icon name="filter" size={16} /> Фільтри{chips.length ? ` · ${chips.length}` : ""}
          </Button>
          <label className="flex items-center gap-2">
            <span className="t-small text-text-muted">Сортування</span>
            <select value={params.get("ordering") ?? ""} onChange={(e) => set("ordering", e.target.value || null)}
              className="min-h-11 cursor-pointer border-b border-line-strong bg-transparent pr-2 focus:outline-none">
              {SORT_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </label>
        </div>
      </div>
      {chips.length > 0 ? (
        <ul className="flex flex-wrap items-center gap-2" aria-label="Активні фільтри">
          {chips.map(([key, value]) => (
            <li key={`${key}-${value}`}>
              <Chip onRemove={() => set(key, null)}>{(CHIP_LABELS[key] ?? ((v: string) => v))(value)}</Chip>
            </li>
          ))}
          <li><button type="button" onClick={clear} className="link t-small px-2">Скинути все</button></li>
        </ul>
      ) : null}
      <Dialog open={open} onOpenChange={setOpen} title="Фільтри">
        <Panel facets={facets} />
        <Button fullWidth onClick={() => setOpen(false)}>Показати {count}</Button>
      </Dialog>
    </div>
  );
}

function Chip({ children, onRemove }: { children: ReactNode; onRemove: () => void }) {
  return (
    <button type="button" onClick={onRemove}
      className={cn("t-small inline-flex min-h-9 items-center gap-2 rounded-[2px] border border-line px-3 hover:border-text")}
      aria-label={`Прибрати фільтр: ${String(children)}`}>
      {children} <Icon name="close" size={14} />
    </button>
  );
}
