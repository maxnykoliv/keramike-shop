import type { Metadata } from "next";

import { AddressBook } from "@/features/account";

export const metadata: Metadata = { title: "Адреси" };

export default function AccountAddressesPage() {
  return (
    <div className="flex flex-col gap-8">
      <h1 className="t-h2">Адреси доставки</h1>
      <AddressBook />
    </div>
  );
}
