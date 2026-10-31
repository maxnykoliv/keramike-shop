/**
 * Дані магазину. Контакти поки порожні: їх надасть замовник (відкрите питання в ТЗ).
 * Порожні поля на сайті не показуються.
 */
export const site = {
  name: "Keramike",
  title: "Keramike — кераміка й калькулятор ремонту",
  description: "Плитка й керамограніт для ванної, кухні та тераси. Порахуйте ремонт онлайн: упаковки, клей, затирка, робота.",
  phone: process.env.NEXT_PUBLIC_SHOP_PHONE ?? "",
  email: process.env.NEXT_PUBLIC_SHOP_EMAIL ?? "",
  address: process.env.NEXT_PUBLIC_SHOP_ADDRESS ?? "",
  hours: process.env.NEXT_PUBLIC_SHOP_HOURS ?? "",
  nav: [
    { href: "/catalog", label: "Каталог" },
    { href: "/calculator", label: "Калькулятор" },
    { href: "/delivery", label: "Доставка й оплата" },
    { href: "/contacts", label: "Контакти" },
  ],
};
