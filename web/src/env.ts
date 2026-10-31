import { z } from "zod";

/** Змінні сервера. Перевіряються при першому зверненні; без обов'язкових сайт не стартує. */
const serverSchema = z.object({
  API_URL: z.string().url().default("http://127.0.0.1:8000"),
  SITE_URL: z.string().url().default("http://localhost:3000"),
  REVALIDATE_SECRET: z.string().optional(),
  /** Спільний секрет з бекендом (BFF_SHARED_SECRET): лише з ним Django вірить X-Client-IP. */
  BFF_SECRET: z.string().optional(),
});

let cached: z.infer<typeof serverSchema> | null = null;

export function serverEnv() {
  if (!cached) {
    const parsed = serverSchema.safeParse(process.env);
    if (!parsed.success) {
      throw new Error(`Некоректні змінні середовища: ${parsed.error.message}`);
    }
    cached = parsed.data;
  }
  return cached;
}

/** Публічні змінні: Next вбудовує їх у бандл під час збірки. */
export const publicEnv = {
  turnstileSiteKey: process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY ?? "",
  gaId: process.env.NEXT_PUBLIC_GA_ID ?? "",
  mediaUrl: process.env.NEXT_PUBLIC_MEDIA_URL ?? "",
};
