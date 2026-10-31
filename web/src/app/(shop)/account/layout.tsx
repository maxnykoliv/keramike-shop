import type { Metadata } from "next";
import type { ReactNode } from "react";

import { AccountNav } from "@/features/account";

export const metadata: Metadata = { title: { default: "Кабінет", template: "%s — кабінет Keramike" }, robots: { index: false, follow: false } };

export default function AccountLayout({ children }: { children: ReactNode }) {
  return (
    <div className="container-page grid gap-8 py-10 md:grid-cols-[200px_1fr] md:gap-16 md:py-14">
      <AccountNav />
      <div className="min-w-0">{children}</div>
    </div>
  );
}
