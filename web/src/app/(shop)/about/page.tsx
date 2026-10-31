import type { Metadata } from "next";

import { ButtonLink } from "@/shared/ui";

export const metadata: Metadata = { title: "Про нас", alternates: { canonical: "/about" } };

export default function AboutPage() {
  return (
    <article className="container-page flex max-w-3xl flex-col gap-8 py-10 md:py-14">
      <h1 className="t-h1">Про Keramike</h1>
      <p className="text-lg text-text-muted">
        Ми продаємо плитку й керамограніт і допомагаємо порахувати ремонт заздалегідь: скільки упаковок узяти,
        скільки клею й затирки знадобиться і скільки коштуватиме робота майстра.
      </p>
      <p className="text-text-muted">
        Для майстрів — окремі ціни в особистому кабінеті. Статус майстра підтверджує менеджер.
      </p>
      <ButtonLink href="/catalog">До каталогу</ButtonLink>
    </article>
  );
}
