"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { useSession } from "@/features/auth";
import { CartCount } from "@/features/cart";
import { site } from "@/shared/config/site";
import { cn } from "@/shared/lib/cn";
import { Dialog, Icon, Logo } from "@/shared/ui";

function AccountLink() {
  const { customer, isMaster } = useSession();
  return (
    <Link href={customer ? "/account" : "/login"} className="relative grid size-11 place-items-center"
      aria-label={customer ? "Кабінет" : "Увійти"} data-testid="account-link">
      <Icon name="user" size={22} />
      {customer ? <span className="absolute top-2 right-2 size-1.5 rounded-full bg-accent" aria-hidden="true" /> : null}
      {isMaster ? <span className="sr-only">Ціни для майстрів</span> : null}
    </Link>
  );
}

function SearchForm({ onDone, className }: { onDone?: () => void; className?: string }) {
  const router = useRouter();
  const [q, setQ] = useState("");
  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (q.trim().length < 2) return;
    router.push(`/search?q=${encodeURIComponent(q.trim())}`);
    onDone?.();
  };
  return (
    <form role="search" onSubmit={submit} className={cn("flex items-center border-b border-line-strong", className)}>
      <label className="sr-only" htmlFor="site-search">Пошук плитки</label>
      <input id="site-search" type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Пошук плитки"
        className="min-h-10 w-full bg-transparent focus:outline-none" />
      <button type="submit" className="grid size-10 place-items-center" aria-label="Шукати"><Icon name="search" /></button>
    </form>
  );
}

export function Header() {
  const pathname = usePathname();
  const { isMaster } = useSession();
  const [menu, setMenu] = useState(false);
  return (
    <header className="sticky top-0 z-30 border-b border-line bg-bg/95 backdrop-blur">
      {isMaster ? (
        <p className="t-label bg-surface py-1.5 text-center text-accent-strong" data-testid="master-banner">Ціни для майстрів</p>
      ) : null}
      <div className="container-page flex h-16 items-center justify-between gap-6 md:h-20">
        <div className="flex items-center gap-2">
          <button type="button" className="-ml-2 grid size-11 place-items-center md:hidden" aria-label="Меню"
            onClick={() => setMenu(true)}><Icon name="menu" /></button>
          <Logo />
        </div>
        <nav aria-label="Головне меню" className="hidden md:block">
          <ul className="flex gap-8">
            {site.nav.map((item) => (
              <li key={item.href}>
                <Link href={item.href} aria-current={pathname.startsWith(item.href) ? "page" : undefined}
                  className={cn("t-label py-2", pathname.startsWith(item.href) ? "border-b border-text" : "text-text-muted hover:text-text")}>
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
        <div className="flex items-center gap-1">
          <SearchForm className="mr-4 hidden w-56 lg:flex" />
          <Link href="/search" className="grid size-11 place-items-center lg:hidden" aria-label="Пошук"><Icon name="search" size={22} /></Link>
          <AccountLink />
          <CartCount />
        </div>
      </div>
      <Dialog open={menu} onOpenChange={setMenu} title="Меню">
        <SearchForm onDone={() => setMenu(false)} className="mb-8" />
        <ul className="flex flex-col">
          {site.nav.map((item) => (
            <li key={item.href} className="border-b border-line">
              <Link href={item.href} onClick={() => setMenu(false)} className="t-h3 flex min-h-14 items-center justify-between">
                {item.label} <Icon name="chevron" />
              </Link>
            </li>
          ))}
        </ul>
      </Dialog>
    </header>
  );
}
