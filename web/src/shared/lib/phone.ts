/** Те саме правило, що й у бекенді (core/phone.py): номер у форматі E.164. */
export function normalizePhone(value: string): string | null {
  const raw = (value ?? "").trim();
  let digits = raw.replace(/\D/g, "");
  if (digits.length === 10 && digits.startsWith("0")) digits = "38" + digits;
  else if (digits.length === 9) digits = "380" + digits;
  if (digits.startsWith("380") && digits.length === 12) return "+" + digits;
  if (raw.startsWith("+") && digits.length >= 10 && digits.length <= 15) return "+" + digits;
  return null;
}

/** +380671234567 → «+380 67 123 45 67». */
export function formatPhone(value: string): string {
  const m = /^\+380(\d{2})(\d{3})(\d{2})(\d{2})$/.exec(value);
  return m ? `+380 ${m[1]} ${m[2]} ${m[3]} ${m[4]}` : value;
}
