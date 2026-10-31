"use client";

import { useState } from "react";

import { bff } from "@/shared/api/client";
import { friendlyMessage } from "@/shared/api/errors";
import { Button, Notice } from "@/shared/ui";

export function PayButton({ token }: { token: string }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pay = async () => {
    setBusy(true);
    setError(null);
    try {
      const { payment_url } = await bff<{ payment_url: string }>(`orders/${token}/pay`, { method: "POST" });
      window.location.assign(payment_url);
    } catch (e) {
      setError(friendlyMessage(e));
      setBusy(false);
    }
  };
  return (
    <div className="flex flex-col gap-3">
      <Button onClick={pay} loading={busy}>Оплатити замовлення</Button>
      {error ? <Notice tone="error">{error}</Notice> : null}
    </div>
  );
}
