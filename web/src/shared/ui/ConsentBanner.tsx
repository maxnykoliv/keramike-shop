"use client";

import { useSyncExternalStore } from "react";

import { CONSENT_KEY } from "@/shared/lib/analytics";

import { Button } from "./Button";

const EVENT = "kr-consent";

function subscribe(onChange: () => void) {
  window.addEventListener(EVENT, onChange);
  window.addEventListener("storage", onChange);
  return () => {
    window.removeEventListener(EVENT, onChange);
    window.removeEventListener("storage", onChange);
  };
}

function needsConsent(): boolean {
  try {
    return !window.localStorage.getItem(CONSENT_KEY);
  } catch {
    return false;
  }
}

/** Consent for analytics cookies. Without consent no events are sent to GA4. */
export function ConsentBanner() {
  const visible = useSyncExternalStore(subscribe, needsConsent, () => false);
  if (!visible) return null;
  const decide = (value: "granted" | "denied") => {
    try {
      window.localStorage.setItem(CONSENT_KEY, value);
    } catch {
      /* storage unavailable: the banner just disappears until reload */
    }
    window.dispatchEvent(new Event(EVENT));
  };
  return (
    <div role="region" aria-label="Згода на cookies" data-testid="consent-banner"
      className="fixed inset-x-4 bottom-4 z-30 border border-line bg-bg p-4 md:left-auto md:right-8 md:bottom-8 md:max-w-md md:p-6">
      <p className="t-small mb-4">
        Ми використовуємо аналітичні cookies, щоб робити сайт зручнішим. Особисті дані до аналітики не потрапляють.
      </p>
      <div className="flex gap-3">
        <Button size="sm" onClick={() => decide("granted")}>Погоджуюсь</Button>
        <Button size="sm" variant="secondary" onClick={() => decide("denied")}>Відмовитись</Button>
      </div>
    </div>
  );
}
