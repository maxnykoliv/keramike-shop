"use client";

import Script from "next/script";
import { useEffect, useId } from "react";

import { publicEnv } from "@/env";

type TurnstileWindow = Window & {
  turnstile?: { render: (el: string, opts: { sitekey: string; callback: (t: string) => void; appearance: string }) => void };
};

/** Invisible form spam protection. Renders nothing without a key (development, tests). */
export function Turnstile({ onToken }: { onToken: (token: string) => void }) {
  const id = `ts${useId().replace(/:/g, "")}`;
  const key = publicEnv.turnstileSiteKey;
  useEffect(() => {
    if (!key) return;
    const w = window as TurnstileWindow;
    const timer = setInterval(() => {
      if (w.turnstile) {
        clearInterval(timer);
        w.turnstile.render(`#${id}`, { sitekey: key, callback: onToken, appearance: "interaction-only" });
      }
    }, 200);
    return () => clearInterval(timer);
  }, [id, key, onToken]);
  if (!key) return null;
  return (
    <>
      <Script src="https://challenges.cloudflare.com/turnstile/v0/api.js" strategy="lazyOnload" />
      <div id={id} />
    </>
  );
}
