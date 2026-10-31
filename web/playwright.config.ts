import { defineConfig, devices } from "@playwright/test";

/**
 * E2E на справжньому стеку: Django (демо-дані, фейкова оплата) + зібраний Next.js.
 * Порти окремі від dev-серверів, щоб тести не чіпали робочу базу.
 */
const WEB_PORT = Number(process.env.E2E_WEB_PORT ?? 3100);
const API_PORT = Number(process.env.E2E_API_PORT ?? 8010);
export const SITE_URL = `http://localhost:${WEB_PORT}`;

export default defineConfig({
  testDir: "./e2e",
  outputDir: "./test-results/e2e",
  timeout: 45_000,
  expect: { timeout: 10_000 },
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 2 : 4,
  reporter: process.env.CI ? [["github"], ["html", { open: "never" }]] : [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: SITE_URL,
    locale: "uk-UA",
    timezoneId: "Europe/Kyiv",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] } },
    { name: "mobile", use: { ...devices["Pixel 7"] } },
  ],
  webServer: [
    {
      command: "./e2e/backend.sh",
      url: `http://127.0.0.1:${API_PORT}/health`,
      env: { E2E_API_PORT: String(API_PORT), E2E_SITE_URL: SITE_URL },
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      stdout: "ignore",
      stderr: "pipe",
    },
    {
      command: process.env.E2E_SKIP_BUILD ? `npx next start -p ${WEB_PORT}` : `npx next build && npx next start -p ${WEB_PORT}`,
      url: SITE_URL,
      env: { API_URL: `http://127.0.0.1:${API_PORT}`, SITE_URL, REVALIDATE_SECRET: "e2e-revalidate" },
      reuseExistingServer: !process.env.CI,
      timeout: 300_000,
      stdout: "ignore",
      stderr: "pipe",
    },
  ],
});
