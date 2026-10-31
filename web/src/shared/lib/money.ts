const NBSP = " ";

function group(whole: string): string {
  const parts: string[] = [];
  for (let i = whole.length; i > 0; i -= 3) parts.unshift(whole.slice(Math.max(0, i - 3), i));
  return parts.join(NBSP);
}

/** 280800 → «2 808,00 грн». Формат збігається з бекендом. */
export function formatUah(kop: number, { withCents = true }: { withCents?: boolean } = {}): string {
  const sign = kop < 0 ? "-" : "";
  const abs = Math.abs(Math.round(kop));
  const whole = group(String(Math.floor(abs / 100)));
  const cents = String(abs % 100).padStart(2, "0");
  return withCents ? `${sign}${whole},${cents}${NBSP}грн` : `${sign}${whole}${NBSP}грн`;
}

/** Ціна за одиницю: «650 грн/м²». */
export function formatUnitPrice(kop: number, unit: string): string {
  const units: Record<string, string> = { m2: "м²", pcs: "шт", bag: "мішок", bucket: "відро", pack: "уп." };
  const value = kop % 100 === 0 ? formatUah(kop, { withCents: false }) : formatUah(kop);
  return `${value}/${units[unit] ?? unit}`;
}
