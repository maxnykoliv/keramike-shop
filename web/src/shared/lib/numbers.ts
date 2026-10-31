/** "2,5" → "2.5". Returns null if it is not a number. */
export function parseDecimal(value: string | number | null | undefined): string | null {
  if (value === null || value === undefined) return null;
  const text = String(value).trim().replace(/\s/g, "").replace(",", ".");
  if (!text || !/^-?\d*\.?\d+$/.test(text)) return null;
  return text;
}

/** «3.40» → «3,40». */
export const formatDecimal = (value: string | number) => String(value).replace(".", ",");

export const formatArea = (value: string | number) => `${formatDecimal(value)} м²`;

const UNIT_LABELS: Record<string, string> = {
  pack: "уп.", m2: "м²", kg: "кг", l: "л", pcs: "шт", bag: "міш.", bucket: "відро",
};
export const unitLabel = (unit: string) => UNIT_LABELS[unit] ?? unit;

export function pluralUk(n: number, forms: [string, string, string]): string {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return forms[0];
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return forms[1];
  return forms[2];
}
