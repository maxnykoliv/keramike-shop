import Link from "next/link";
import { connection } from "next/server";

import { ProductGrid } from "@/features/catalog";
import { getProducts } from "@/features/catalog/server";
import { ButtonLink, TileSwatch } from "@/shared/ui";

const ROOMS = [
  { slug: "bathroom", title: "Ванна", color: "білий", size: [300, 600] },
  { slug: "kitchen", title: "Кухня", color: "беж", size: [200, 200] },
  { slug: "hallway", title: "Коридор", color: "сірий", size: [600, 600] },
  { slug: "terrace", title: "Тераса", color: "коричневий", size: [600, 1200] },
] as const;

const STEPS = [
  { title: "Оберіть плитку", text: "Розмір, колір, поверхня — фільтри в каталозі." },
  { title: "Вкажіть площу", text: "Розміри кімнати або квадратуру, вікна й двері." },
  { title: "Отримайте кошторис", text: "Упаковки, клей, затирка й робота — з цінами." },
];

export default async function HomePage() {
  await connection();
  const fresh = await getProducts(new URLSearchParams({ ordering: "-new", kind: "tile" })).catch(() => null);
  return (
    <>
      <section className="container-page grid items-center gap-10 py-12 md:grid-cols-[1.1fr_1fr] md:py-24">
        <div className="fade-up flex flex-col gap-8">
          <p className="t-label text-accent-strong">Плитка й керамограніт</p>
          <h1 className="t-display">Ремонт, порахований до упаковки</h1>
          <p className="max-w-md text-lg text-text-muted">
            Оберіть плитку, вкажіть розміри кімнати — калькулятор порахує упаковки, клей, затирку та вартість роботи.
          </p>
          <div className="flex flex-wrap gap-3">
            <ButtonLink href="/calculator" size="lg" data-testid="hero-calculator">Порахувати ремонт</ButtonLink>
            <ButtonLink href="/catalog" size="lg" variant="secondary">Каталог</ButtonLink>
          </div>
        </div>
        <div className="grid grid-cols-6 grid-rows-6 gap-2" aria-hidden="true">
          <TileSwatch width={600} height={1200} color="білий" className="col-span-3 row-span-6" />
          <TileSwatch width={300} height={300} color="беж" className="col-span-3 row-span-3" />
          <TileSwatch width={200} height={200} color="дерево" className="col-span-3 row-span-3" />
        </div>
      </section>

      <section aria-labelledby="rooms-title" className="container-page py-16">
        <h2 id="rooms-title" className="t-h2 mb-10">Для якої кімнати</h2>
        <ul className="grid grid-cols-2 gap-4 md:grid-cols-4 md:gap-8">
          {ROOMS.map((room) => (
            <li key={room.slug}>
              <Link href={`/catalog?room=${room.slug}`} className="group flex flex-col gap-3">
                <div className="aspect-[4/5] overflow-hidden">
                  <TileSwatch width={room.size[0]} height={room.size[1]} color={room.color} className="img-zoom size-full" />
                </div>
                <span className="t-h3 flex items-center justify-between">{room.title}<span aria-hidden="true">→</span></span>
              </Link>
            </li>
          ))}
        </ul>
      </section>

      <section aria-labelledby="steps-title" className="bg-surface py-20">
        <div className="container-page">
          <h2 id="steps-title" className="t-h2 mb-12">Калькулятор за три кроки</h2>
          <ol className="grid gap-10 md:grid-cols-3">
            {STEPS.map((step, i) => (
              <li key={step.title} className="flex flex-col gap-3 border-t border-line-strong pt-6">
                <span className="t-label text-accent-strong">0{i + 1}</span>
                <h3 className="t-h3">{step.title}</h3>
                <p className="text-text-muted">{step.text}</p>
              </li>
            ))}
          </ol>
          <ButtonLink href="/calculator" className="mt-12">Відкрити калькулятор</ButtonLink>
        </div>
      </section>

      {fresh && fresh.results.length > 0 ? (
        <section aria-labelledby="new-title" className="container-page py-20">
          <div className="mb-10 flex items-end justify-between gap-4">
            <h2 id="new-title" className="t-h2">Нове в каталозі</h2>
            <Link href="/catalog?ordering=-new" className="link">Усі товари</Link>
          </div>
          <ProductGrid initial={{ results: fresh.results.slice(0, 6), next: null }} />
        </section>
      ) : null}
    </>
  );
}
