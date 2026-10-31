import "server-only";

import { redirect } from "next/navigation";

import { ApiError } from "@/shared/api/errors";
import { accountGet } from "@/shared/api/server";

/** Account data. If the session expired, go to login and come back to the same page. */
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
