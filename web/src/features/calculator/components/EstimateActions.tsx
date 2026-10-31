"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { useCartActions } from "@/features/cart";
import { bff } from "@/shared/api/client";
import { friendlyMessage } from "@/shared/api/errors";
import type { PdfStatus } from "@/shared/api/types";
import { Button, ButtonLink, Icon, Notice } from "@/shared/ui";

/** Actions on a saved estimate page. */
export function EstimateActions({ code, canAddToCart }: { code: string; canAddToCart: boolean }) {
  const router = useRouter();
  const { fromEstimate } = useCartActions();
  const [error, setError] = useState<string | null>(null);
  const [pdfState, setPdfState] = useState<"idle" | "busy" | "rendering">("idle");

  const add = async () => {
    setError(null);
    try {
      await fromEstimate.mutateAsync(code);
      router.push("/cart");
    } catch (e) {
      setError(friendlyMessage(e));
    }
  };
  const pdf = async () => {
    setPdfState("busy");
    try {
      const status = await bff<PdfStatus>(`calc/estimates/${code}/pdf`);
      if (status.status === "ready" && status.url) {
        window.open(status.url, "_blank", "noopener");
        setPdfState("idle");
      } else setPdfState("rendering");
    } catch (e) {
      setError(friendlyMessage(e));
      setPdfState("idle");
    }
  };
  return (
    <div className="flex flex-col gap-3">
      {canAddToCart ? <Button onClick={add} loading={fromEstimate.isPending} fullWidth>Додати все у кошик</Button> : null}
      <ButtonLink href={`/calculator?estimate=${code}`} variant="secondary" fullWidth>
        <Icon name="calculator" size={16} /> Перерахувати в калькуляторі
      </ButtonLink>
      <Button variant="ghost" onClick={pdf} loading={pdfState === "busy"}><Icon name="download" size={16} /> Завантажити PDF</Button>
      {pdfState === "rendering" ? <Notice tone="info">PDF ще готується, спробуйте за хвилину.</Notice> : null}
      {error ? <Notice tone="error">{error}</Notice> : null}
    </div>
  );
}
