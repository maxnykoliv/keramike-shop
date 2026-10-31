"use client";

import { useRef } from "react";

import { bff } from "@/shared/api/client";
import type { EstimateCreated, PdfStatus } from "@/shared/api/types";
import { track } from "@/shared/lib/analytics";

import { formFingerprint, toServerPayload, type CalcForm } from "../model";

/**
 * Actions on the result. The estimate is saved on the server once per unchanged form:
 * add to cart, share, PDF and lead all reuse the same code.
 */
export function useEstimateActions(form: CalcForm) {
  const saved = useRef<{ fingerprint: string; titled: boolean; estimate: EstimateCreated } | null>(null);

  const save = async (title = ""): Promise<EstimateCreated> => {
    const fingerprint = formFingerprint(form);
    if (saved.current?.fingerprint === fingerprint && (!title || saved.current.titled)) return saved.current.estimate;
    const estimate = await bff<EstimateCreated>("calc/estimates", {
      method: "POST", body: { ...toServerPayload(form), source: "calculator", title },
    });
    saved.current = { fingerprint, titled: Boolean(title), estimate };
    track("estimate_saved", { total: estimate.result.total_kop / 100 });
    return estimate;
  };

  const shareUrl = (code: string) => `${window.location.origin}/calculator/${code}`;

  /** The PDF is rendered in the background: poll for up to 15 seconds. */
  const pdf = async (code: string): Promise<string | null> => {
    for (let attempt = 0; attempt < 15; attempt++) {
      const status = await bff<PdfStatus>(`calc/estimates/${code}/pdf`);
      if (status.status === "ready" && status.url) {
        track("estimate_pdf");
        return status.url;
      }
      await new Promise((r) => setTimeout(r, 1000));
    }
    return null;
  };

  return { save, shareUrl, pdf };
}
