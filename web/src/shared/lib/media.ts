import { publicEnv } from "@/env";

/** The backend returns relative paths for local storage and absolute URLs for R2. */
export function mediaUrl(path: string | null | undefined): string | null {
  if (!path) return null;
  if (/^https?:\/\//.test(path)) return path;
  return `${publicEnv.mediaUrl}${path}`;
}
