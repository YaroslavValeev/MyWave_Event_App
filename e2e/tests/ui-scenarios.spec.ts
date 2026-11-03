/**
 * Browser smoke — requires web at E2E_WEB_BASE (default :3000).
 */
import { expect, test } from "@playwright/test";

const WEB = process.env.E2E_WEB_BASE || "http://127.0.0.1:3000";

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
});
