import { expect, test } from "@playwright/test";

test("production shell redirects to sign-in or renders an authenticated dashboard", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveURL(/\/(auth\/signin)?(\?.*)?$/);
  await expect(page.locator("body")).not.toContainText(/access_token|refresh_token|SELECT .* FROM/i);
});

test("open redirect payload remains on the application origin", async ({ page }) => {
  await page.goto("/auth/signin?callbackUrl=https://evil.example");
  expect(new URL(page.url()).origin).toBe(new URL(test.info().project.use.baseURL as string).origin);
});
