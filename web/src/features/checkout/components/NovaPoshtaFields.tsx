"use client";

import { useQuery } from "@tanstack/react-query";
import { useEffect, useId, useState } from "react";

import { bff } from "@/shared/api/client";
import { friendlyMessage } from "@/shared/api/errors";
import type { City, Warehouse } from "@/shared/api/types";
import { Field, Notice, Select, Spinner, TextInput } from "@/shared/ui";

export type NpValue = { cityRef: string; cityName: string; warehouseRef: string; warehouseName: string };

function useDebounced(value: string, ms = 300) {
  const [v, setV] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return v;
}

/** City with search and a branch list. The backend caches the reference data; TanStack Query caches it here. */
export function NovaPoshtaFields({ value, onChange, errors }: {
  value: NpValue;
  onChange: (value: NpValue) => void;
  errors?: { city?: string; warehouse?: string };
}) {
  const [query, setQuery] = useState(value.cityName);
  const [open, setOpen] = useState(false);
  const listId = `cities${useId()}`;
  const q = useDebounced(query.trim());
  const cities = useQuery({
    queryKey: ["np-cities", q],
    queryFn: () => bff<City[]>(`delivery/np/cities?q=${encodeURIComponent(q)}`),
    enabled: open && q.length >= 2 && q !== value.cityName,
    staleTime: 60 * 60_000,
  });
  const warehouses = useQuery({
    queryKey: ["np-warehouses", value.cityRef],
    queryFn: () => bff<Warehouse[]>(`delivery/np/warehouses?city=${encodeURIComponent(value.cityRef)}`),
    enabled: Boolean(value.cityRef),
    staleTime: 60 * 60_000,
  });

  const pickCity = (city: City) => {
    setQuery(city.name);
    setOpen(false);
    onChange({ cityRef: city.ref, cityName: city.name, warehouseRef: "", warehouseName: "" });
  };

  return (
    <div className="flex flex-col gap-5">
      <div className="relative">
        <Field label="Місто" error={errors?.city}>
          {(ids) => (
            <TextInput ids={ids} role="combobox" aria-expanded={open && Boolean(cities.data?.length)} aria-controls={listId}
              aria-autocomplete="list" autoComplete="off" placeholder="Почніть вводити назву" value={query}
              data-testid="np-city"
              onChange={(e) => { setQuery(e.target.value); setOpen(true); if (value.cityRef) onChange({ cityRef: "", cityName: "", warehouseRef: "", warehouseName: "" }); }} />
          )}
        </Field>
        {cities.isFetching ? <span className="absolute top-9 right-0"><Spinner label="Шукаємо місто" /></span> : null}
        {open && cities.data && cities.data.length > 0 ? (
          <ul id={listId} role="listbox" className="absolute inset-x-0 z-10 mt-1 max-h-64 overflow-y-auto border border-line bg-bg">
            {cities.data.map((city) => (
              <li key={city.ref} role="option" aria-selected={false}>
                <button type="button" onClick={() => pickCity(city)} className="w-full px-4 py-3 text-left hover:bg-surface">
                  {city.name}
                </button>
              </li>
            ))}
          </ul>
        ) : null}
        {cities.isError ? <Notice tone="error" className="mt-2">{friendlyMessage(cities.error)}</Notice> : null}
      </div>
      <Field label="Відділення або поштомат" error={errors?.warehouse}>
        {(ids) => (
          <Select ids={ids} disabled={!value.cityRef || warehouses.isLoading} value={value.warehouseRef} data-testid="np-warehouse"
            onChange={(e) => {
              const w = warehouses.data?.find((x) => x.ref === e.target.value);
              onChange({ ...value, warehouseRef: w?.ref ?? "", warehouseName: w?.name ?? "" });
            }}>
            <option value="">{value.cityRef ? (warehouses.isLoading ? "Завантажуємо…" : "Оберіть відділення") : "Спершу оберіть місто"}</option>
            {warehouses.data?.map((w) => <option key={w.ref} value={w.ref}>{w.name}</option>)}
          </Select>
        )}
      </Field>
    </div>
  );
}
