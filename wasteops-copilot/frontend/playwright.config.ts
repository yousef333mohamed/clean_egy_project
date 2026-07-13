import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  use: { baseURL: "http://127.0.0.1:3000", trace: "on-first-retry" },
  webServer: {
    command: "npm run dev",
    url: "http://127.0.0.1:3000",
    reuseExistingServer: !process.env.CI,
    env: {
      NEXT_PUBLIC_APP_NAME: "WasteOps Decision Intelligence Copilot",
      NEXT_PUBLIC_API_BASE_URL: "http://localhost:8000",
      NEXT_PUBLIC_APP_ENV: "test",
      NEXT_PUBLIC_ENABLE_ADMIN_PAGES: "true",
      NEXT_PUBLIC_ENABLE_INGESTION_PAGES: "true",
      NEXT_PUBLIC_ENABLE_EVALUATION_PAGES: "true",
      NEXT_PUBLIC_ENABLE_PROMPT_PAGES: "true",
      NEXT_PUBLIC_DEFAULT_LANGUAGE: "en",
      NEXT_PUBLIC_DEFAULT_TIMEZONE: "Africa/Cairo",
    },
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
    { name: "mobile", use: { ...devices["Pixel 7"] } },
  ],
});
