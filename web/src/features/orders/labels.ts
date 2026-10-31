export const ORDER_STEPS = [
  { status: "new", label: "Нове" },
  { status: "confirmed", label: "Підтверджене" },
  { status: "packed", label: "Зібране" },
  { status: "shipped", label: "Відправлене" },
  { status: "completed", label: "Виконане" },
] as const;

export const DELIVERY_LABELS: Record<string, string> = { pickup: "Самовивіз", local: "Доставка по місту", nova_poshta: "Нова пошта" };
export const PAYMENT_LABELS: Record<string, string> = { online: "Карткою онлайн", cod: "При отриманні", invoice: "Рахунок для юросіб" };
