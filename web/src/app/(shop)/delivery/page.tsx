import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Доставка й оплата",
  description: "Самовивіз, доставка по місту й Новою поштою. Оплата карткою онлайн, при отриманні або за рахунком.",
  alternates: { canonical: "/delivery" },
};

const SECTIONS = [
  { title: "Самовивіз", text: "Безкоштовно зі складу після підтвердження замовлення менеджером." },
  { title: "Доставка по місту", text: "Вартість залежить від ваги й адреси — менеджер назве її під час дзвінка." },
  { title: "Нова пошта", text: "У відділення по всій Україні. Вартість рахуємо за вагою замовлення ще під час оформлення." },
  { title: "Оплата", text: "Карткою онлайн, при отриманні або за рахунком для юридичних осіб." },
  { title: "Повернення", text: "Цілі упаковки без слідів монтажу можна повернути протягом 14 днів. Плитку під замовлення не повертаємо." },
];

export default function DeliveryPage() {
  return (
    <article className="container-page flex max-w-3xl flex-col gap-10 py-10 md:py-14">
      <h1 className="t-h1">Доставка й оплата</h1>
      {SECTIONS.map((s) => (
        <section key={s.title} className="flex flex-col gap-2 border-t border-line pt-6">
          <h2 className="t-h3">{s.title}</h2>
          <p className="text-text-muted">{s.text}</p>
        </section>
      ))}
    </article>
  );
}
