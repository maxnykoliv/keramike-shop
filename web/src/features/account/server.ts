import "server-only";

import { redirect } from "next/navigation";

import { ApiError } from "@/shared/api/errors";
import { accountGet } from "@/shared/api/server";

/** Дані кабінету. Сесія скінчилася — на вхід із поверненням на ту саму сторінку. */
export async function accountData<T>(path: string, back: string): Promise<T> {
  try {
    return await accountGet<T>(path);
  } catch (e) {
    if (e instanceof ApiError && (e.status === 401 || e.status === 403)) {
      redirect(`/login?next=${encodeURIComponent(back)}`);
    }
    throw e;
  }
}
