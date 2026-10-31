"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";

import { NovaPoshtaFields, type NpValue } from "@/features/checkout";
import { bff } from "@/shared/api/client";
import { flattenFieldErrors, friendlyMessage, isApiError } from "@/shared/api/errors";
import type { Address } from "@/shared/api/types";
import { Badge, Button, Field, Notice, RadioCards, Skeleton, TextInput } from "@/shared/ui";

const EMPTY_NP: NpValue = { cityRef: "", cityName: "", warehouseRef: "", warehouseName: "" };

export function AddressBook() {
  const client = useQueryClient();
  const addresses = useQuery({ queryKey: ["addresses"], queryFn: () => bff<Address[]>("account/addresses") });
  const refresh = () => client.invalidateQueries({ queryKey: ["addresses"] });
  const makeDefault = useMutation({
    mutationFn: (id: number) => bff(`account/addresses/${id}`, { method: "PATCH", body: { is_default: true } }),
    onSuccess: refresh,
  });
  const remove = useMutation({
    mutationFn: (id: number) => bff(`account/addresses/${id}`, { method: "DELETE" }),
    onSuccess: refresh,
  });
  const [adding, setAdding] = useState(false);

  if (addresses.isLoading) return <Skeleton className="h-40" />;
  const list = addresses.data ?? [];
  return (
    <div className="flex flex-col gap-8">
      {list.length === 0 && !adding ? <p className="text-text-muted">Збережених адрес ще немає.</p> : null}
      <ul className="divide-y divide-line border-y border-line" aria-label="Адреси">
        {list.map((a) => (
          <li key={a.id} className="flex flex-wrap items-start justify-between gap-4 py-5" data-testid="address">
            <div className="flex flex-col gap-1">
              <p className="flex items-center gap-2 font-medium">
                {a.label || (a.delivery_method === "nova_poshta" ? "Нова пошта" : "Доставка по місту")}
                {a.is_default ? <Badge tone="accent">Основна</Badge> : null}
              </p>
              <p className="text-text-muted">
                {a.delivery_method === "nova_poshta" ? `${a.city_name}, ${a.warehouse_name}` : a.address}
              </p>
            </div>
            <div className="flex gap-2">
              {!a.is_default ? (
                <Button variant="ghost" size="sm" onClick={() => makeDefault.mutate(a.id)}>Зробити основною</Button>
              ) : null}
              <Button variant="ghost" size="sm" onClick={() => remove.mutate(a.id)} aria-label={`Видалити адресу ${a.label || a.address || a.warehouse_name}`}>
                Видалити
              </Button>
            </div>
          </li>
        ))}
      </ul>
      {adding ? <AddressForm onDone={() => { setAdding(false); refresh(); }} onCancel={() => setAdding(false)} /> : (
        <Button variant="secondary" onClick={() => setAdding(true)} className="self-start">Додати адресу</Button>
      )}
    </div>
  );
}

function AddressForm({ onDone, onCancel }: { onDone: () => void; onCancel: () => void }) {
  const [method, setMethod] = useState<"local" | "nova_poshta">("nova_poshta");
  const [label, setLabel] = useState("");
  const [address, setAddress] = useState("");
  const [np, setNp] = useState<NpValue>(EMPTY_NP);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setErrors({});
    setError(null);
    try {
      await bff("account/addresses", {
        method: "POST",
        body: method === "local"
          ? { delivery_method: method, label, address }
          : { delivery_method: method, label, city_ref: np.cityRef, city_name: np.cityName, warehouse_ref: np.warehouseRef, warehouse_name: np.warehouseName },
      });
      onDone();
    } catch (e) {
      if (isApiError(e) && e.errors) setErrors(flattenFieldErrors(e.errors));
      else setError(friendlyMessage(e));
      setBusy(false);
    }
  };

  return (
    <form onSubmit={submit} className="flex flex-col gap-5 border border-line p-5" noValidate data-testid="address-form">
      <RadioCards legend="Спосіб доставки" name="address-method" value={method} onChange={setMethod}
        options={[{ value: "nova_poshta", label: "Нова пошта" }, { value: "local", label: "По місту" }]} />
      <Field label="Назва" hint="Необов'язково, напр. «Дім» або «Дача»">
        {(ids) => <TextInput ids={ids} value={label} onChange={(e) => setLabel(e.target.value)} />}
      </Field>
      {method === "local" ? (
        <Field label="Адреса" error={errors.address}>
          {(ids) => <TextInput ids={ids} autoComplete="street-address" value={address} onChange={(e) => setAddress(e.target.value)} />}
        </Field>
      ) : (
        <NovaPoshtaFields value={np} onChange={setNp} errors={{ warehouse: errors.warehouse_ref }} />
      )}
      {error ? <Notice tone="error">{error}</Notice> : null}
      <div className="flex gap-3">
        <Button type="submit" loading={busy}>Зберегти адресу</Button>
        <Button variant="ghost" onClick={onCancel}>Скасувати</Button>
      </div>
    </form>
  );
}
