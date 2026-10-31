import "server-only";

import { serverEnv } from "@/env";

export const SESSION_COOKIE = "kr_session";
export const CART_COOKIE = "kr_cart";
export const LOGIN_COOKIE = "kr_login";

export const SESSION_MAX_AGE = 60 * 60 * 24 * 60;
export const CART_MAX_AGE = 60 * 60 * 24 * 30;
export const LOGIN_MAX_AGE = 60 * 10;

/** httpOnly + SameSite=Lax; Secure — коли сайт працює через HTTPS. */
export function cookieOptions(maxAge: number) {
  return {
    httpOnly: true,
    sameSite: "lax" as const,
    secure: serverEnv().SITE_URL.startsWith("https://"),
    path: "/",
    maxAge,
  };
}
