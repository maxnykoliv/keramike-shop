"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { Controller, useForm, useWatch } from "react-hook-form";
import { z } from "zod";

import { useSession } from "@/features/auth";
import { CART_KEY, useCart } from "@/features/cart";
import { bff, request } from "@/shared/api/client";
import { flattenFieldErrors, friendlyMessage, isApiError } from "@/shared/api/errors";
import type { Address, CheckoutResult } from "@/shared/api/types";
import { track } from "@/shared/lib/analytics";
import { formatUah } from "@/shared/lib/money";
import { normalizePhone } from "@/shared/lib/phone";
import { readJson, removeKey, writeJson } from "@/shared/lib/storage";
import { Button, ButtonLink, Checkbox, Field, Notice, RadioCards, Skeleton, TextArea, TextInput, Turnstile } from "@/shared/ui";

import { NovaPoshtaFields } from "./NovaPoshtaFields";

const schema = z.object({
  name: z.string().trim().min(2, "Вкажіть ім'я та прізвище"),
  phone: z.string().refine((v) => normalizePhone(v) !== null, "Вкажіть номер у форматі +380 67 123 45 67"),
  email: z.union([z.literal(""), z.string().email("Некоректний email")]),
  comment: z.string().max(2000),
  delivery_method: z.enum(["pickup", "local", "nova_poshta"]),
  address: z.string().max(500),
  np: z.object({ cityRef: z.string(), cityName: z.string(), warehouseRef: z.string(), warehouseName: z.string() }),
  payment_method: z.enum(["online", "cod", "invoice"]),
  save_address: z.boolean(),
  agree: z.literal(true, { error: "Потрібна згода з політикою конфіденційності" }),
}).superRefine((v, ctx) => {
  if (v.delivery_method === "local" && !v.address.trim()) ctx.addIssue({ code: "custom", path: ["address"], message: "Вкажіть адресу доставки" });
  if (v.delivery_method === "nova_poshta" && !v.np.cityRef) ctx.addIssue({ code: "custom", path: ["np", "cityRef"], message: "Оберіть місто зі списку" });
  if (v.delivery_method === "nova_poshta" && v.np.cityRef && !v.np.warehouseRef) ctx.addIssue({ code: "custom", path: ["np", "warehouseRef"], message: "Оберіть відділення" });
});
type Values = z.infer<typeof schema>;

const DRAFT_KEY = "kr_checkout_draft";
const IDEMPOTENCY_KEY = "kr_checkout_key";

type Quote = { quote_id: string; cost_kop: number | null };

export function CheckoutForm() {
  const router = useRouter();
  const client = useQueryClient();
  const { data: cart, isLoading } = useCart();
  const { customer } = useSession();
  const addresses = useQuery({
    queryKey: ["addresses"],
    queryFn: () => bff<Address[]>("account/addresses"),
    enabled: Boolean(customer),
  });
  const [error, setError] = useState<string | null>(null);
  const [captcha, setCaptcha] = useState("");

  const { register, control, handleSubmit, setValue, setError: setFieldError, getValues, formState, reset } = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: "", phone: "", email: "", comment: "", delivery_method: "pickup", address: "",
      np: { cityRef: "", cityName: "", warehouseRef: "", warehouseName: "" },
      payment_method: "online", save_address: false, agree: false as unknown as true,
      ...readJson<Partial<Values>>(DRAFT_KEY, "session"),
    },
  });
  const values = useWatch({ control });

  // Prefill the logged-in customer's details and their default address.
  useEffect(() => {
    if (!customer) return;
    const current = getValues();
    if (!current.name) setValue("name", customer.name ?? "");
    if (!current.phone) setValue("phone", customer.phone);
    if (!current.email) setValue("email", customer.email ?? "");
  }, [customer, getValues, setValue]);
  useEffect(() => {
    const main = addresses.data?.find((a) => a.is_default);
    if (!main || getValues("address") || getValues("np.cityRef")) return;
    setValue("delivery_method", main.delivery_method);
    if (main.delivery_method === "local") setValue("address", main.address ?? "");
    else setValue("np", { cityRef: main.city_ref ?? "", cityName: main.city_name ?? "", warehouseRef: main.warehouse_ref ?? "", warehouseName: main.warehouse_name ?? "" });
  }, [addresses.data, getValues, setValue]);

  useEffect(() => {
    const timer = setTimeout(() => {
      const { agree: _agree, ...draft } = getValues();
      void _agree;
      writeJson(DRAFT_KEY, draft, "session");
    }, 300);
    return () => clearTimeout(timer);
  }, [values, getValues]);

  // Delivery cost: the backend quotes it; the site shows it and passes quote_id to the order.
  const method = values.delivery_method;
  const cityRef = values.np?.cityRef;
  const quoteQuery = useQuery({
    queryKey: ["delivery-quote", method, cityRef ?? "", cart?.subtotal_kop, cart?.lines.length],
    queryFn: () => request<Quote>("/api/cart/quote", { method: "POST", body: { method, city_ref: cityRef ?? "" } }),
    enabled: Boolean(cart?.lines.length && method && method !== "pickup" && (method !== "nova_poshta" || cityRef)),
    retry: false,
  });
  const quote = quoteQuery.data ?? null;
  const quoteLoading = quoteQuery.isFetching;

  // Without a selected city there is no Nova Poshta quote.
  const activeQuote = method === "pickup" || (method === "nova_poshta" && !cityRef) ? null : quote;

  const idempotencyKey = useMemo(() => {
    const existing = readJson<string>(IDEMPOTENCY_KEY, "session");
    if (existing) return existing;
    const key = crypto.randomUUID();
    writeJson(IDEMPOTENCY_KEY, key, "session");
    return key;
  }, []);

  const submit = handleSubmit(async (v) => {
    setError(null);
    const delivery = v.delivery_method === "nova_poshta"
      ? { city_ref: v.np.cityRef, city_name: v.np.cityName, warehouse_ref: v.np.warehouseRef, warehouse_name: v.np.warehouseName }
      : v.delivery_method === "local" ? { address: v.address } : {};
    try {
      const result = await request<CheckoutResult>("/api/checkout", {
        method: "POST",
        headers: { "Idempotency-Key": idempotencyKey },
        body: {
          name: v.name, phone: normalizePhone(v.phone), email: v.email, comment: v.comment,
          delivery_method: v.delivery_method, delivery, payment_method: v.payment_method,
          quote_id: activeQuote?.quote_id ?? "", captcha,
        },
      });
      if (customer && v.save_address && v.delivery_method !== "pickup") {
        await bff("account/addresses", {
          method: "POST",
          body: { delivery_method: v.delivery_method, address: v.address, city_ref: v.np.cityRef, city_name: v.np.cityName,
            warehouse_ref: v.np.warehouseRef, warehouse_name: v.np.warehouseName, label: "" },
        }).catch(() => undefined);
      }
      track("purchase", { value: result.total_kop / 100 });
      removeKey(IDEMPOTENCY_KEY, "session");
      removeKey(DRAFT_KEY, "session");
      reset();
      await client.invalidateQueries({ queryKey: CART_KEY });
      if (result.payment_url) window.location.assign(result.payment_url);
      else router.push(`/orders/${result.public_token}${result.payment_retry ? "?pay=retry" : ""}`);
    } catch (e) {
      if (isApiError(e) && e.code === "validation_error") {
        const fields = flattenFieldErrors(e.errors);
        for (const [path, message] of Object.entries(fields)) {
          const name = path.startsWith("delivery") ? "address" : path;
          if (["name", "phone", "email", "address", "comment"].includes(name)) setFieldError(name as keyof Values, { message });
        }
        setError("Перевірте поля форми.");
      } else setError(friendlyMessage(e));
    }
  });

  if (isLoading) return <Skeleton className="h-[480px]" />;
  if (!cart || cart.lines.length === 0) {
    return (
      <div className="flex flex-col items-start gap-6" data-testid="checkout-empty">
        <p className="t-h2">Кошик порожній</p>
        <ButtonLink href="/catalog">До каталогу</ButtonLink>
      </div>
    );
  }

  const deliveryKop = method === "pickup" ? 0 : activeQuote?.cost_kop ?? null;
  const errors = formState.errors;
  return (
    <form onSubmit={submit} noValidate className="grid gap-12 md:grid-cols-[1fr_380px] md:items-start md:gap-16">
      <div className="flex flex-col gap-12">
        <section aria-labelledby="contacts" className="flex flex-col gap-5">
          <h2 id="contacts" className="t-h3">1. Контакти</h2>
          {!customer ? (
            <p className="t-small text-text-muted">
              <Link href="/login?next=/checkout" className="link">Увійдіть</Link>, щоб замовлення з’явилося в кабінеті, — або просто заповніть форму.
            </p>
          ) : null}
          <Field label="Ім'я та прізвище" error={errors.name?.message}>
            {(ids) => <TextInput ids={ids} autoComplete="name" {...register("name")} />}
          </Field>
          <Field label="Телефон" error={errors.phone?.message}>
            {(ids) => <TextInput ids={ids} type="tel" inputMode="tel" autoComplete="tel" placeholder="+380 67 123 45 67" {...register("phone")} />}
          </Field>
          <Field label="Email" hint="Необов'язково: надішлемо підтвердження" error={errors.email?.message}>
            {(ids) => <TextInput ids={ids} type="email" autoComplete="email" {...register("email")} />}
          </Field>
          <Field label="Коментар" hint="Необов'язково">
            {(ids) => <TextArea ids={ids} rows={3} {...register("comment")} />}
          </Field>
        </section>

        <section aria-labelledby="delivery" className="flex flex-col gap-5">
          <h2 id="delivery" className="t-h3">2. Доставка</h2>
          <Controller control={control} name="delivery_method" render={({ field }) => (
            <RadioCards legend="Спосіб доставки" name="delivery_method" value={field.value} onChange={field.onChange} columns={3}
              options={[
                { value: "pickup", label: "Самовивіз", description: "Безкоштовно, зі складу" },
                { value: "local", label: "По місту", description: "Нашим транспортом" },
                { value: "nova_poshta", label: "Нова пошта", description: "У відділення" },
              ]} />
          )} />
          {method === "local" ? (
            <Field label="Адреса доставки" error={errors.address?.message}>
              {(ids) => <TextInput ids={ids} autoComplete="street-address" placeholder="Вулиця, будинок, квартира" {...register("address")} />}
            </Field>
          ) : null}
          {method === "nova_poshta" ? (
            <Controller control={control} name="np" render={({ field }) => (
              <NovaPoshtaFields value={field.value} onChange={field.onChange}
                errors={{ city: errors.np?.cityRef?.message, warehouse: errors.np?.warehouseRef?.message }} />
            )} />
          ) : null}
          {customer && method !== "pickup" ? <Checkbox label="Запам'ятати адресу" {...register("save_address")} /> : null}
        </section>

        <section aria-labelledby="payment" className="flex flex-col gap-5">
          <h2 id="payment" className="t-h3">3. Оплата</h2>
          <Controller control={control} name="payment_method" render={({ field }) => (
            <RadioCards legend="Спосіб оплати" name="payment_method" value={field.value} onChange={field.onChange} columns={3}
              options={[
                { value: "online", label: "Карткою онлайн", description: "Apple Pay, Google Pay" },
                { value: "cod", label: "При отриманні", description: "Готівкою або карткою" },
                { value: "invoice", label: "Рахунок", description: "Для юросіб" },
              ]} />
          )} />
        </section>
      </div>

      <aside aria-labelledby="summary" className="flex flex-col gap-5 border-t border-line pt-6 md:sticky md:top-28 md:border md:p-6">
        <h2 id="summary" className="t-h3">Ваше замовлення</h2>
        <ul className="flex flex-col gap-2 t-small">
          {cart.lines.map((line) => (
            <li key={line.id} className="flex justify-between gap-4">
              <span>{line.name} × {line.qty}</span>
              <span className="tabular shrink-0">{line.total_display}</span>
            </li>
          ))}
        </ul>
        <dl className="flex flex-col gap-2 border-t border-line pt-4">
          <div className="flex justify-between"><dt>Товари</dt><dd className="tabular">{formatUah(cart.subtotal_kop)}</dd></div>
          <div className="flex justify-between"><dt>Доставка</dt>
            <dd className="tabular" data-testid="delivery-cost">
              {quoteLoading ? "рахуємо…" : deliveryKop === null ? "уточнить менеджер" : deliveryKop === 0 ? "безкоштовно" : formatUah(deliveryKop)}
            </dd>
          </div>
          <div className="flex items-baseline justify-between"><dt className="font-semibold">Разом</dt>
            <dd className="t-price" data-testid="checkout-total">{formatUah(cart.subtotal_kop + (deliveryKop ?? 0))}</dd>
          </div>
        </dl>
        <Checkbox {...register("agree")}
          label={<>Погоджуюсь з <Link href="/privacy" className="link" target="_blank">політикою конфіденційності</Link></>} />
        {errors.agree ? <p role="alert" className="t-small text-error">{errors.agree.message}</p> : null}
        <Turnstile onToken={setCaptcha} />
        {error ? <Notice tone="error">{error}</Notice> : null}
        <Button type="submit" loading={formState.isSubmitting} fullWidth>Підтвердити замовлення</Button>
        <p className="t-small text-text-muted">Менеджер зателефонує, щоб підтвердити наявність і доставку.</p>
      </aside>
    </form>
  );
}
