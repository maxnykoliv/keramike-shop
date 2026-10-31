import type { Metadata } from "next";

import { site } from "@/shared/config/site";
import { ButtonLink } from "@/shared/ui";

export const metadata: Metadata = { title: "Контакти", alternates: { canonical: "/contacts" } };

export default function ContactsPage() {
  const rows = [
    { label: "Телефон", value: site.phone, href: site.phone ? `tel:${site.phone.replace(/[^\d+]/g, "")}` : undefined },
    { label: "Пошта", value: site.email, href: site.email ? `mailto:${site.email}` : undefined },
    { label: "Адреса", value: site.address },
    { label: "Графік", value: site.hours },
  ].filter((r) => r.value);
  return (
    <div className="container-page flex max-w-3xl flex-col gap-10 py-10 md:py-14">
      <h1 className="t-h1">Контакти</h1>
      {rows.length ? (
        <dl className="flex flex-col">
          {rows.map((r) => (
            <div key={r.label} className="flex flex-col gap-1 border-t border-line py-5 md:flex-row md:gap-10">
              <dt className="t-label w-32 text-text-muted">{r.label}</dt>
              <dd className="text-lg">{r.href ? <a className="link" href={r.href}>{r.value}</a> : r.value}</dd>
            </div>
          ))}
        </dl>
      ) : (
        <p className="text-text-muted">Залиште заявку з калькулятора — менеджер передзвонить і відповість на питання.</p>
      )}
      <ButtonLink href="/calculator" variant="secondary">Порахувати ремонт</ButtonLink>
    </div>
  );
}
