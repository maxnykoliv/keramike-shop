import type { Metadata } from "next";

export const metadata: Metadata = { title: "Політика конфіденційності", alternates: { canonical: "/privacy" } };

const SECTIONS = [
  { title: "Які дані ми збираємо", text: "Ім’я, телефон, email і адресу доставки — лише ті, що ви вказуєте під час замовлення, заявки або входу." },
  { title: "Навіщо", text: "Щоб оформити й доставити замовлення, зв’язатися з вами щодо кошторису та показати історію в кабінеті." },
  { title: "Кому передаємо", text: "Службі доставки — для відправлення, платіжному сервісу — для оплати. Більше нікому." },
  { title: "Аналітика", text: "Знеособлену статистику відвідувань збираємо лише після вашої згоди в банері cookie." },
  { title: "Ваші права", text: "Ви можете попросити показати, виправити або видалити ваші дані — напишіть нам через сторінку контактів." },
];

export default function PrivacyPage() {
  return (
    <article className="container-page flex max-w-3xl flex-col gap-8 py-10 md:py-14">
      <h1 className="t-h1">Політика конфіденційності</h1>
      {SECTIONS.map((s) => (
        <section key={s.title} className="flex flex-col gap-2">
          <h2 className="t-h3">{s.title}</h2>
          <p className="text-text-muted">{s.text}</p>
        </section>
      ))}
    </article>
  );
}
