/** Funnel events (see the frontend spec). Sent to GA4 only after cookie consent. */
export type AnalyticsEvent =
  | "calculator_start" | "calculator_result" | "estimate_saved" | "estimate_shared"
  | "estimate_pdf" | "generate_lead" | "add_to_cart" | "begin_checkout" | "purchase" | "login";

export const CONSENT_KEY = "kr_consent";

type DataLayerWindow = Window & { dataLayer?: unknown[] };

export function hasConsent(): boolean {
  try {
    return typeof window !== "undefined" && window.localStorage.getItem(CONSENT_KEY) === "granted";
  } catch {
    return false;
  }
}

export function track(event: AnalyticsEvent, params: Record<string, string | number | boolean> = {}): void {
  if (typeof window === "undefined") return;
  // Personal data (name, phone, email) is never sent to analytics.
  const w = window as DataLayerWindow;
  w.dataLayer = w.dataLayer ?? [];
  if (hasConsent()) w.dataLayer.push({ event, ...params });
}
