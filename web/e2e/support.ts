import { createHmac, randomInt } from "node:crypto";
import { readFile } from "node:fs/promises";
import path from "node:path";

import { expect, test as base, type APIRequestContext, type BrowserContext, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

export const API = `http://127.0.0.1:${process.env.E2E_API_PORT ?? 8010}/api/v1`;
const TELEGRAM_SECRET = process.env.E2E_TELEGRAM_SECRET ?? "e2e-telegram-secret";
const PAYMENT_KEY = process.env.E2E_PAYMENT_KEY ?? "e2e-payment-key";
const OUTBOX = process.env.E2E_OUTBOX ?? path.join(__dirname, "..", "test-results", "auth-outbox.txt");

export const MASTER_PHONE = "+380670000001";

/** Демо-товари з seed_demo. */
export const TILE = { slug: "crs-mg-6060", name: "Marble Grey 60×60", priceKop: 65000, masterKop: 55250 };
export const WALL_TILE = { slug: "crs-ww-3060", name: "White Wave 30×60" };

/** Унікальний номер для кожного тесту: ліміт кодів рахується на телефон. */
export const randomPhone = () => `+38063${String(randomInt(0, 10_000_000)).padStart(7, "0")}`;

/** Розбивка на тисячі вузьким нерозривним пробілом, як у formatUah. */
export const uah = (kop: number) => {
  const whole = String(Math.floor(kop / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  return `${whole},${String(kop % 100).padStart(2, "0")} грн`;
};

type Fixtures = { consent: void };

export const test = base.extend<Fixtures>({
  // Банер cookies закриває кнопки на телефоні — у більшості тестів погоджуємось заздалегідь.
  consent: [async ({ context }, use) => {
    await context.addInitScript(() => {
      try { window.localStorage.setItem("kr_consent", "denied"); } catch { /* ignore */ }
    });
    // Посилання на бота відкривається в новій вкладці — у тестах без виходу в інтернет.
    await context.route(/^https:\/\/t\.me\//, (route) => route.fulfill({ body: "<html><body>telegram</body></html>", contentType: "text/html" }));
    await use();
  }, { auto: true }],
});

export { expect };

export const isMobile = (page: Page) => (page.viewportSize()?.width ?? 1280) < 768;

export async function telegramUpdate(request: APIRequestContext, message: Record<string, unknown>) {
  const response = await request.post(`${API}/auth/telegram/webhook`, {
    headers: { "X-Telegram-Bot-Api-Secret-Token": TELEGRAM_SECRET },
    data: { update_id: randomInt(1, 1e9), message },
  });
  expect(response.ok()).toBeTruthy();
}

/** Те, що робить Telegram: /start з токеном, потім контакт власного номера. */
export async function confirmInTelegram(request: APIRequestContext, botUrl: string, phone: string) {
  const token = new URL(botUrl).searchParams.get("start");
  expect(token).toBeTruthy();
  const userId = randomInt(1, 2 ** 31);
  const from = { id: userId, first_name: "Тест", username: `u${userId}` };
  const chat = { id: userId, type: "private" };
  await telegramUpdate(request, { message_id: 1, from, chat, date: 0, text: `/start ${token}` });
  await telegramUpdate(request, {
    message_id: 2, from, chat, date: 0,
    contact: { phone_number: phone.replace("+", ""), first_name: "Тест", user_id: userId },
  });
}

/** Вхід без UI: ті самі маршрути Next.js, cookie лягають у контекст браузера. */
export async function loginAs(context: BrowserContext, phone: string, baseURL: string) {
  const headers = { Origin: baseURL };
  const start = await context.request.post(`${baseURL}/api/auth/telegram/start`, { headers });
  expect(start.ok()).toBeTruthy();
  const { bot_url: botUrl } = await start.json();
  await confirmInTelegram(context.request, botUrl, phone);
  const poll = await context.request.post(`${baseURL}/api/auth/telegram/poll`, { headers });
  expect((await poll.json()).status).toBe("confirmed");
}

/** Код із «консольного» каналу: бекенд пише його у файл. */
export async function readCode(phone: string): Promise<string> {
  let code: string | undefined;
  await expect.poll(async () => {
    const text = await readFile(OUTBOX, "utf8").catch(() => "");
    code = text.trim().split("\n").reverse().find((line) => line.startsWith(`${phone} `))?.split(" ")[1];
    return code;
  }, { message: `код для ${phone}` }).toBeTruthy();
  return code!;
}

/** Підпис як у FakeProvider: HMAC-SHA256 від JSON з відсортованими ключами. */
export async function payWebhook(request: APIRequestContext, reference: string, amountKop: number, status = "succeeded") {
  const payload = { amount_kop: amountKop, reference, status };
  const signature = createHmac("sha256", PAYMENT_KEY).update(JSON.stringify(payload)).digest("hex");
  const response = await request.post(`${API}/payments/webhook/fake`, { data: { payload, signature } });
  expect(response.ok()).toBeTruthy();
}

/** Кошик через API сайту: швидко підготувати стан для тестів оформлення. */
export async function addToCart(context: BrowserContext, baseURL: string, slug: string, qty: number) {
  const product = await (await context.request.get(`${API}/catalog/products/${slug}`)).json();
  const response = await context.request.post(`${baseURL}/api/cart/items`, {
    headers: { Origin: baseURL }, data: { product_id: product.id, qty },
  });
  expect(response.ok(), await response.text()).toBeTruthy();
  return product as { id: number; price_kop: number; m2_per_pack: string | null };
}

export async function expectNoA11yViolations(page: Page) {
  const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
  const serious = results.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
  expect(serious.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(" ")).join(", ")}`)).toEqual([]);
}
