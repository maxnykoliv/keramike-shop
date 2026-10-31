"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { useRefreshAfterAuth } from "@/features/auth";
import { bff, request } from "@/shared/api/client";
import { friendlyMessage } from "@/shared/api/errors";
import type { Customer } from "@/shared/api/types";
import { formatPhone } from "@/shared/lib/phone";
import { Badge, Button, Field, Notice, TextInput } from "@/shared/ui";

const schema = z.object({
  name: z.string().trim().max(150),
  email: z.union([z.literal(""), z.string().email("Некоректний email")]),
});

export function ProfileForm({ customer }: { customer: Customer }) {
  const router = useRouter();
  const refresh = useRefreshAfterAuth();
  const [status, setStatus] = useState<{ tone: "success" | "error"; text: string } | null>(null);
  const [leaving, setLeaving] = useState<"one" | "all" | null>(null);
  const { register, handleSubmit, formState } = useForm<z.infer<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues: { name: customer.name ?? "", email: customer.email ?? "" },
  });

  const save = handleSubmit(async (values) => {
    setStatus(null);
    try {
      await bff("account/me", { method: "PATCH", body: values });
      await refresh();
      setStatus({ tone: "success", text: "Збережено." });
      router.refresh();
    } catch (e) {
      setStatus({ tone: "error", text: friendlyMessage(e) });
    }
  });

  const logout = async (all: boolean) => {
    setLeaving(all ? "all" : "one");
    await request("/api/auth/logout", { method: "POST", body: { all } }).catch(() => undefined);
    await refresh();
    router.replace("/");
    router.refresh();
  };

  return (
    <div className="flex flex-col gap-12">
      <form onSubmit={save} className="flex max-w-md flex-col gap-5" noValidate>
        <dl className="flex flex-col gap-1">
          <dt className="t-small text-text-muted">Телефон</dt>
          <dd className="tabular" data-testid="profile-phone">{formatPhone(customer.phone)}</dd>
          {customer.telegram_username ? <dd className="t-small text-text-muted">Telegram: @{customer.telegram_username}</dd> : null}
          {customer.is_master ? <dd className="mt-2"><Badge tone="accent">Майстер</Badge></dd> : null}
        </dl>
        <Field label="Ім'я" error={formState.errors.name?.message}>
          {(ids) => <TextInput ids={ids} autoComplete="name" {...register("name")} />}
        </Field>
        <Field label="Email" error={formState.errors.email?.message}>
          {(ids) => <TextInput ids={ids} type="email" autoComplete="email" {...register("email")} />}
        </Field>
        {status ? <Notice tone={status.tone}>{status.text}</Notice> : null}
        <Button type="submit" loading={formState.isSubmitting} className="self-start">Зберегти</Button>
      </form>
      <section aria-labelledby="sessions" className="flex flex-col gap-4 border-t border-line pt-8">
        <h2 id="sessions" className="t-h3">Вихід</h2>
        <div className="flex flex-wrap gap-3">
          <Button variant="secondary" onClick={() => logout(false)} loading={leaving === "one"}>Вийти</Button>
          <Button variant="ghost" onClick={() => logout(true)} loading={leaving === "all"}>Вийти на всіх пристроях</Button>
        </div>
      </section>
    </div>
  );
}
