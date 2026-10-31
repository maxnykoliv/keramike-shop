import Link from "next/link";

import { site } from "@/shared/config/site";
import { Logo } from "@/shared/ui";

export function Footer() {
  const contacts = [site.phone, site.email, site.address, site.hours].filter(Boolean);
  return (
    <footer className="mt-32 bg-surface">
      <div className="container-page grid gap-12 py-16 md:grid-cols-[2fr_1fr_1fr]">
        <div className="flex flex-col gap-4">
          <Logo />
          <p className="max-w-sm text-text-muted">{site.description}</p>
        </div>
        <nav aria-label="Меню у футері">
          <p className="t-label mb-4 text-text-muted">Магазин</p>
          <ul className="flex flex-col gap-2">
            {[...site.nav, { href: "/about", label: "Про нас" }].map((item) => (
              <li key={item.href}><Link href={item.href} className="hover:text-accent-strong">{item.label}</Link></li>
            ))}
          </ul>
        </nav>
        <div>
          <p className="t-label mb-4 text-text-muted">Контакти</p>
          {contacts.length ? (
            <ul className="flex flex-col gap-2">{contacts.map((c) => <li key={c}>{c}</li>)}</ul>
          ) : (
            <Link href="/contacts" className="link">Зв’язатися з нами</Link>
          )}
        </div>
      </div>
      <div className="container-page t-small flex flex-wrap justify-between gap-4 border-t border-line py-6 text-text-muted">
        <p>© {new Date().getFullYear()} {site.name}</p>
        <Link href="/privacy" className="hover:text-text">Політика конфіденційності</Link>
      </div>
    </footer>
  );
}
