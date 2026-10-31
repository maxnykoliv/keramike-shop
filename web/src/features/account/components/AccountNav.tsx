"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/shared/lib/cn";

const LINKS = [
  { href: "/account", label: "Огляд" },
  { href: "/account/orders", label: "Замовлення" },
  { href: "/account/estimates", label: "Кошториси" },
  { href: "/account/addresses", label: "Адреси" },
  { href: "/account/profile", label: "Профіль" },
];

export function AccountNav() {
  const pathname = usePathname();
  return (
    <nav aria-label="Кабінет" className="-mx-4 overflow-x-auto px-4 md:mx-0 md:px-0">
      <ul className="flex gap-6 border-b border-line md:flex-col md:gap-1 md:border-0">
        {LINKS.map((link) => {
          const active = pathname === link.href;
          return (
            <li key={link.href}>
              <Link href={link.href} aria-current={active ? "page" : undefined}
                className={cn("block whitespace-nowrap py-3 md:py-2",
                  active ? "border-b-2 border-text md:border-0 md:font-semibold" : "text-text-muted hover:text-text")}>
                {link.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
