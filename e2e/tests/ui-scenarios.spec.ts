/**
 * Browser smoke — requires web at E2E_WEB_BASE (default :3000).
 * Staging tunnel example: E2E_WEB_BASE=http://127.0.0.1:13001
 */
import { expect, test } from "@playwright/test";

const WEB = process.env.E2E_WEB_BASE || "http://127.0.0.1:3000";
const EVENT_ID = process.env.E2E_EVENT_ID || "1";

test.describe("UI smoke", () => {
  test.beforeAll(async ({ request }) => {
    try {
      const res = await request.get(WEB);
      test.skip(!res.ok(), `Web not reachable at ${WEB}`);
    } catch {
      test.skip(true, `Web not reachable at ${WEB}`);
    }
  });

  test("home page loads in Russian", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("body")).toContainText(/Champ|MyWave|Событ|мероприят/i);
  });

  test("events list opens", async ({ page }) => {
    await page.goto("/events");
    await expect(page.locator("body")).toBeVisible();
  });

  test("event page opens", async ({ page }) => {
    await page.goto(`/events/${EVENT_ID}`);
    await expect(page.locator("body")).toBeVisible();
    await expect(page.locator("body")).toContainText(/Казан|Отчёт|событ|Champ|MyWave|заявк|состав/i);
  });
});
