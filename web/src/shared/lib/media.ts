import { publicEnv } from "@/env";

/** Бекенд віддає відносні шляхи для локального сховища і повні — для R2. */
export function mediaUrl(path: string | null | undefined): string | null {
  if (!path) return null;
  if (/^https?:\/\//.test(path)) return path;
  return `${publicEnv.mediaUrl}${path}`;
}
