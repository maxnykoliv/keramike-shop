"use client";

import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { QRCodeSVG } from "qrcode.react";
import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";

import { bff, request } from "@/shared/api/client";
import { friendlyMessage } from "@/shared/api/errors";
import type { AuthMethods, Customer } from "@/shared/api/types";
import { track } from "@/shared/lib/analytics";
import { normalizePhone } from "@/shared/lib/phone";
import { Button, Field, Icon, Notice, TextInput } from "@/shared/ui";

import { useRefreshAfterAuth } from "../hooks/useSession";

type TelegramState = "idle" | "starting" | "pending" | "awaiting_contact" | "confirmed" | "expired" | "error";

const STATUS_TEXT: Partial<Record<TelegramState, string>> = {
  pending: "Відкрийте бота в Telegram і натисніть «Start».",
  awaiting_contact: "Тепер поділіться номером телефону кнопкою в Telegram.",
  confirmed: "Готово, входимо…",
  expired: "Посилання застаріло. Спробуйте ще раз.",
};

export function LoginPanel({ next }: { next: string }) {
  const router = useRouter();
  const refresh = useRefreshAfterAuth();
  const methods = useQuery({ queryKey: ["auth-methods"], queryFn: () => bff<AuthMethods>("auth/methods") });

  const done = useCallback(async () => {
    track("login");
    await refresh();
    router.replace(next);
    router.refresh();
  }, [next, refresh, router]);

  return (
    <div className="flex flex-col gap-10">
      <TelegramLogin onDone={done} />
      {methods.data && methods.data.code_channels.length > 0 ? (
        <CodeLogin channel={methods.data.code_channels[0]!} onDone={done} />
      ) : null}
    </div>
  );
}

function TelegramLogin({ onDone }: { onDone: () => Promise<void> }) {
  const [state, setState] = useState<TelegramState>("idle");
  const [botUrl, setBotUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const polling = useRef(false);

  const poll = useCallback(async () => {
    if (polling.current) return;
    polling.current = true;
    try {
      const result = await request<{ status: TelegramState; customer?: Customer }>("/api/auth/telegram/poll", { method: "POST" });
      setState(result.status);
      if (result.status === "confirmed") await onDone();
    } catch {
      /* мережа зникла — спробуємо на наступному кроці */
    } finally {
      polling.current = false;
    }
  }, [onDone]);

  useEffect(() => {
    if (state !== "pending" && state !== "awaiting_contact") return;
    const timer = setInterval(poll, 2000);
    const onVisible = () => document.visibilityState === "visible" && poll();
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      clearInterval(timer);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [state, poll]);

  const start = async () => {
    setError(null);
    setState("starting");
    // Вікно відкриваємо синхронно з кліком, інакше браузер його заблокує.
    const tab = typeof window !== "undefined" ? window.open("", "_blank") : null;
    try {
      const data = await request<{ bot_url: string }>("/api/auth/telegram/start", { method: "POST" });
      setBotUrl(data.bot_url);
      setState("pending");
      if (tab) tab.location.href = data.bot_url;
    } catch (e) {
      tab?.close();
      setError(friendlyMessage(e));
      setState("error");
    }
  };

  const active = state === "pending" || state === "awaiting_contact";
  return (
    <section aria-labelledby="tg-title" className="flex flex-col gap-5">
      <h2 id="tg-title" className="t-h3">Через Telegram</h2>
      <p className="text-text-muted">Без пароля: бот підтвердить ваш номер телефону. Це займає кілька секунд.</p>
      {!active ? (
        <Button onClick={start} loading={state === "starting"} fullWidth>
          <Icon name="telegram" /> Увійти через Telegram
        </Button>
      ) : null}
      {active && botUrl ? (
        <div className="flex flex-col gap-5 border border-line p-5 md:flex-row md:items-center">
          <div className="hidden shrink-0 bg-bg p-2 md:block" aria-hidden="true">
            <QRCodeSVG value={botUrl} size={132} bgColor="transparent" fgColor="currentColor" />
          </div>
          <div className="flex flex-col gap-3">
            <p role="status" aria-live="polite" data-testid="telegram-status">{STATUS_TEXT[state]}</p>
            <p className="t-small text-text-muted md:block">На комп’ютері відскануйте QR-код телефоном або відкрийте посилання.</p>
            <a href={botUrl} target="_blank" rel="noopener noreferrer" className="link" data-testid="telegram-link">
              Відкрити бота в Telegram
            </a>
          </div>
        </div>
      ) : null}
      {state === "expired" ? <Notice>{STATUS_TEXT.expired}</Notice> : null}
      {error ? <Notice tone="error">{error}</Notice> : null}
    </section>
  );
}

function CodeLogin({ channel, onDone }: { channel: string; onDone: () => Promise<void> }) {
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  const [step, setStep] = useState<"phone" | "code">("phone");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendCode = async (event: FormEvent) => {
    event.preventDefault();
    const normalized = normalizePhone(phone);
    if (!normalized) return setError("Вкажіть номер у форматі +380 67 123 45 67");
    setBusy(true);
    setError(null);
    try {
      await bff("auth/code/request", { method: "POST", body: { phone: normalized, channel } });
      setStep("code");
    } catch (e) {
      setError(friendlyMessage(e));
    } finally {
      setBusy(false);
    }
  };

  const verify = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await request("/api/auth/code/verify", { method: "POST", body: { phone: normalizePhone(phone), code } });
      await onDone();
    } catch (e) {
      setError(friendlyMessage(e));
      setBusy(false);
    }
  };

  return (
    <section aria-labelledby="code-title" className="flex flex-col gap-5 border-t border-line pt-10">
      <h2 id="code-title" className="t-h3">Кодом на телефон</h2>
      {step === "phone" ? (
        <form onSubmit={sendCode} className="flex flex-col gap-5" noValidate>
          <Field label="Телефон" error={error}>
            {(ids) => <TextInput ids={ids} type="tel" inputMode="tel" autoComplete="tel" placeholder="+380 67 123 45 67"
              value={phone} onChange={(e) => setPhone(e.target.value)} />}
          </Field>
          <Button type="submit" variant="secondary" loading={busy}>Надіслати код</Button>
        </form>
      ) : (
        <form onSubmit={verify} className="flex flex-col gap-5" noValidate>
          <Field label="Код із повідомлення" hint="6 цифр. Код діє 10 хвилин." error={error}>
            {(ids) => <TextInput ids={ids} inputMode="numeric" autoComplete="one-time-code" maxLength={6}
              value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))} />}
          </Field>
          <div className="flex flex-wrap gap-3">
            <Button type="submit" loading={busy}>Увійти</Button>
            <Button variant="ghost" onClick={() => { setStep("phone"); setCode(""); setError(null); }}>Змінити номер</Button>
          </div>
        </form>
      )}
    </section>
  );
}
