/** Події воронки (див. ТЗ фронтенду). Надсилаються в GA4 лише після згоди на cookies. */
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
  // Особисті дані (ім'я, телефон, email) в аналітику не передаються.
  const w = window as DataLayerWindow;
  w.dataLayer = w.dataLayer ?? [];
  if (hasConsent()) w.dataLayer.push({ event, ...params });
}
