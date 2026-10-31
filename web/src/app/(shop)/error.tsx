"use client";

import { useEffect } from "react";

import { Button, ButtonLink } from "@/shared/ui";

export default function ShopError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => { console.error(error); }, [error]);
  return (
    <div className="container-page flex flex-col items-start gap-6 py-24" role="alert">
      <h1 className="t-h1">Щось пішло не так</h1>
      <p className="max-w-md text-text-muted">Ми вже знаємо про проблему. Спробуйте ще раз за хвилину.</p>
      {error.digest ? <p className="t-small text-text-muted">Код помилки: {error.digest}</p> : null}
      <div className="flex flex-wrap gap-3">
        <Button onClick={reset}>Спробувати ще раз</Button>
        <ButtonLink href="/" variant="secondary">На головну</ButtonLink>
      </div>
    </div>
  );
}
