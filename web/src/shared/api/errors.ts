/** Backend error format: {code, message, field, errors?}. */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly field: string | null;
  readonly errors: Record<string, unknown> | null;
  readonly extra: Record<string, unknown>;

  constructor(status: number, body: Record<string, unknown> | null) {
    const message = typeof body?.message === "string" ? body.message : "Щось пішло не так. Спробуйте ще раз.";
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = typeof body?.code === "string" ? body.code : "error";
    this.field = typeof body?.field === "string" ? body.field : null;
    this.errors = (body?.errors as Record<string, unknown>) ?? null;
    this.extra = body ?? {};
  }
}

export const isApiError = (e: unknown): e is ApiError => e instanceof ApiError;

/** A flat "field path → message" list from DRF's nested structure. */
export function flattenFieldErrors(errors: unknown, prefix = ""): Record<string, string> {
  const out: Record<string, string> = {};
  if (Array.isArray(errors)) {
    if (errors.every((e) => typeof e === "string")) {
      if (prefix) out[prefix] = errors.join(" ");
      return out;
    }
    errors.forEach((item, index) => Object.assign(out, flattenFieldErrors(item, `${prefix}[${index}]`)));
    return out;
  }
  if (errors && typeof errors === "object") {
    for (const [key, value] of Object.entries(errors)) {
      const path = key === "non_field_errors" ? prefix : prefix ? `${prefix}.${key}` : key;
      Object.assign(out, flattenFieldErrors(value, path));
    }
    return out;
  }
  if (typeof errors === "string" && prefix) out[prefix] = errors;
  return out;
}

/** Messages for codes that have their own text in the UI. */
export function friendlyMessage(error: unknown): string {
  if (!isApiError(error)) return "Немає з'єднання. Перевірте інтернет і спробуйте ще раз.";
  switch (error.code) {
    case "out_of_stock":
      return error.message;
    case "payment_required":
      return "Замовлення можна відправити лише після оплати.";
    case "captcha_failed":
      return "Не вдалося підтвердити, що ви не робот. Оновіть сторінку.";
    case "throttled":
      return "Забагато спроб. Зачекайте трохи й повторіть.";
    default:
      return error.message;
  }
}
