import { defineConfig } from "@playwright/test";

const API = process.env.E2E_API_BASE || "http://127.0.0.1:8000";
const WEB = process.env.E2E_WEB_BASE || "http://127.0.0.1:3000";

export default defineConfig({
  testDir: "./tests",
  timeout: 60_000,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: WEB,
    extraHTTPHeaders: {},
  },
  projects: [
    {
      name: "api",
      testMatch: /api-scenarios\.spec\.ts/,
      use: { baseURL: API },
    },
    {
      name: "ui",
      testMatch: /ui-scenarios\.spec\.ts/,
      use: { baseURL: WEB, browserName: "chromium" },
    },
  ],
});
