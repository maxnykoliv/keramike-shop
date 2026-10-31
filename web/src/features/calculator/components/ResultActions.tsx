"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type ReactNode } from "react";

import { useSession } from "@/features/auth";
import { useCartActions } from "@/features/cart";
import { friendlyMessage } from "@/shared/api/errors";
import type { EstimateCreated } from "@/shared/api/types";
import { track } from "@/shared/lib/analytics";
import { formatUah } from "@/shared/lib/money";
import { Button, Dialog, Field, Icon, Notice, TextInput } from "@/shared/ui";

import { useEstimateActions } from "../hooks/useEstimateActions";
import type { CalcForm } from "../model";
import { LeadDialog } from "./LeadDialog";

export function ResultActions({ form, localTotal, disabled }: { form: CalcForm; localTotal: number | null; disabled: boolean }) {
  const router = useRouter();
  const { customer } = useSession();
  const { save, shareUrl, pdf } = useEstimateActions(form);
  const { fromEstimate } = useCartActions();
  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState<{ tone: "success" | "error" | "info"; text: ReactNode } | null>(null);
  const [link, setLink] = useState<string | null>(null);
  const [leadOpen, setLeadOpen] = useState(false);
  const [saveOpen, setSaveOpen] = useState(false);
  const [title, setTitle] = useState("");

  const run = async (name: string, action: () => Promise<void>) => {
    setBusy(name);
    setMessage(null);
    try {
      await action();
    } catch (e) {
      setMessage({ tone: "error", text: friendlyMessage(e) });
    } finally {
      setBusy(null);
    }
  };

  /** The server has the final say. If its total differs, show the server's and explain why. */
  const checkTotal = (estimate: EstimateCreated) => {
    if (localTotal !== null && estimate.result.total_kop !== localTotal) {
      setMessage({ tone: "info", text: `Ціни щойно оновились. Актуальна сума: ${formatUah(estimate.result.total_kop)}.` });
    }
  };

  const addToCart = () => run("cart", async () => {
    const estimate = await save();
    await fromEstimate.mutateAsync(estimate.code);
    checkTotal(estimate);
    router.push("/cart");
  });

  const share = () => run("share", async () => {
    const estimate = await save();
    const url = shareUrl(estimate.code);
    setLink(url);
    track("estimate_shared");
    if (navigator.share) {
      await navigator.share({ title: "Кошторис ремонту Keramike", url }).catch(() => undefined);
    } else {
      await navigator.clipboard?.writeText(url).catch(() => undefined);
      setMessage({ tone: "success", text: "Посилання скопійовано." });
    }
  });

  const downloadPdf = () => run("pdf", async () => {
    const estimate = await save();
    const url = await pdf(estimate.code);
    if (url) window.open(url, "_blank", "noopener");
    else setMessage({ tone: "info", text: <>PDF ще готується. Він з’явиться на сторінці <Link className="link" href={`/calculator/${estimate.code}`}>кошторису</Link>.</> });
  });

  const saveToAccount = () => run("save", async () => {
    const estimate = await save(title.trim() || "Мій розрахунок");
    setSaveOpen(false);
    checkTotal(estimate);
    setMessage({ tone: "success", text: <>Збережено в кабінеті. <Link className="link" href="/account/estimates">Мої кошториси</Link></> });
  });

  return (
    <div className="flex flex-col gap-3" data-testid="result-actions">
      <Button onClick={addToCart} loading={busy === "cart"} disabled={disabled || busy !== null} fullWidth>
        Додати все у кошик
      </Button>
      <div className="grid grid-cols-2 gap-3">
        <Button variant="secondary" size="sm" onClick={share} loading={busy === "share"} disabled={disabled || busy !== null}>
          <Icon name="share" size={16} /> Поділитися
        </Button>
        <Button variant="secondary" size="sm" onClick={downloadPdf} loading={busy === "pdf"} disabled={disabled || busy !== null}>
          <Icon name="download" size={16} /> PDF
        </Button>
      </div>
      <Button variant="ghost" size="sm" onClick={() => setLeadOpen(true)} disabled={disabled}>Надіслати менеджеру</Button>
      {customer ? (
        <Button variant="ghost" size="sm" onClick={() => setSaveOpen(true)} disabled={disabled}>Зберегти в кабінеті</Button>
      ) : (
        <p className="t-small text-center text-text-muted">
          <Link href="/login?next=/calculator" className="link">Увійдіть</Link>, щоб кошториси зберігалися в кабінеті.
        </p>
      )}
      {link ? (
        <label className="flex flex-col gap-1">
          <span className="t-small text-text-muted">Посилання на кошторис</span>
          <input readOnly value={link} onFocus={(e) => e.target.select()} data-testid="share-link"
            className="t-small min-h-10 border-b border-line-strong bg-transparent focus:outline-none" />
        </label>
      ) : null}
      {message ? <Notice tone={message.tone}>{message.text}</Notice> : null}

      <LeadDialog open={leadOpen} onOpenChange={setLeadOpen} getEstimateCode={async () => (await save()).code} />
      <Dialog open={saveOpen} onOpenChange={setSaveOpen} title="Зберегти кошторис">
        <form onSubmit={(e) => { e.preventDefault(); saveToAccount(); }} className="flex flex-col gap-5">
          <Field label="Назва" hint="Наприклад, «Ванна на дачі»">
            {(ids) => <TextInput ids={ids} value={title} maxLength={120} onChange={(e) => setTitle(e.target.value)} autoFocus />}
          </Field>
          <Button type="submit" loading={busy === "save"} fullWidth>Зберегти</Button>
        </form>
      </Dialog>
    </div>
  );
}
