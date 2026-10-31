"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { useSession } from "@/features/auth";
import { bff } from "@/shared/api/client";
import { friendlyMessage } from "@/shared/api/errors";
import { track } from "@/shared/lib/analytics";
import { normalizePhone } from "@/shared/lib/phone";
import { Button, Dialog, Field, Notice, TextArea, TextInput, Turnstile } from "@/shared/ui";

const schema = z.object({
  name: z.string().trim().min(2, "Вкажіть ім'я"),
  phone: z.string().refine((v) => normalizePhone(v) !== null, "Вкажіть номер у форматі +380 67 123 45 67"),
  comment: z.string().max(2000).optional(),
});
type Values = z.infer<typeof schema>;

/** "Send to manager": the estimate is saved and the manager gets a lead in Telegram. */
export function LeadDialog({ open, onOpenChange, getEstimateCode }: {
  open: boolean; onOpenChange: (open: boolean) => void; getEstimateCode: () => Promise<string>;
}) {
  const { customer } = useSession();
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [captcha, setCaptcha] = useState("");
  const { register, handleSubmit, formState } = useForm<Values>({
    resolver: zodResolver(schema),
    values: { name: customer?.name ?? "", phone: customer?.phone ?? "", comment: "" },
  });

  const submit = handleSubmit(async (values) => {
    setError(null);
    try {
      const code = await getEstimateCode();
      await bff("leads", {
        method: "POST",
        body: { name: values.name, phone: normalizePhone(values.phone), comment: values.comment ?? "", estimate_code: code, captcha },
      });
      track("generate_lead");
      setSent(true);
    } catch (e) {
      setError(friendlyMessage(e));
    }
  });

  return (
    <Dialog open={open} onOpenChange={(v) => { onOpenChange(v); if (!v) setSent(false); }}
      title={sent ? "Дякуємо!" : "Надіслати менеджеру"}
      description={sent ? undefined : "Менеджер перевірить розрахунок, наявність і передзвонить."}>
      {sent ? (
        <div className="flex flex-col gap-6" data-testid="lead-success">
          <p>Заявку отримано. Менеджер зв’яжеться з вами найближчим часом.</p>
          <Button onClick={() => onOpenChange(false)}>Добре</Button>
        </div>
      ) : (
        <form onSubmit={submit} className="flex flex-col gap-5" noValidate>
          <Field label="Ім'я" error={formState.errors.name?.message}>
            {(ids) => <TextInput ids={ids} autoComplete="name" {...register("name")} />}
          </Field>
          <Field label="Телефон" error={formState.errors.phone?.message}>
            {(ids) => <TextInput ids={ids} type="tel" inputMode="tel" autoComplete="tel" placeholder="+380 67 123 45 67" {...register("phone")} />}
          </Field>
          <Field label="Коментар" hint="Необов'язково">
            {(ids) => <TextArea ids={ids} rows={3} {...register("comment")} />}
          </Field>
          <Turnstile onToken={setCaptcha} />
          {error ? <Notice tone="error">{error}</Notice> : null}
          <Button type="submit" loading={formState.isSubmitting} fullWidth>Надіслати</Button>
        </form>
      )}
    </Dialog>
  );
}
