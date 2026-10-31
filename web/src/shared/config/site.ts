/**
 * Shop details. Contacts are empty for now: the client will provide them (open question in the spec).
 * Empty fields are not shown on the site.
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
