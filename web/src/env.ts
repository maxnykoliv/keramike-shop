import { z } from "zod";

/** Server variables. Validated on first access; the site does not start without the required ones. */
const serverSchema = z.object({
  API_URL: z.string().url().default("http://127.0.0.1:8000"),
  SITE_URL: z.string().url().default("http://localhost:3000"),
  REVALIDATE_SECRET: z.string().optional(),
  /** Secret shared with the backend (BFF_SHARED_SECRET): Django trusts X-Client-IP only with it. */
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

/** Public variables: Next inlines them into the bundle at build time. */
export const publicEnv = {
  turnstileSiteKey: process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY ?? "",
  gaId: process.env.NEXT_PUBLIC_GA_ID ?? "",
  mediaUrl: process.env.NEXT_PUBLIC_MEDIA_URL ?? "",
};
