import type { Metadata } from "next";
import { connection } from "next/server";

import { ProfileForm } from "@/features/account";
import { accountData } from "@/features/account/server";
import type { Customer } from "@/shared/api/types";

export const metadata: Metadata = { title: "Профіль" };

export default async function AccountProfilePage() {
  await connection();
  const me = await accountData<Customer>("account/me", "/account/profile");
  return (
    <div className="flex flex-col gap-8">
      <h1 className="t-h2">Профіль</h1>
      <ProfileForm customer={me} />
    </div>
  );
}
