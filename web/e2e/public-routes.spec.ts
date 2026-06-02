import { test, expect } from '@playwright/test';

/**
 * Public route matrix — no auth required.
 */
const PUBLIC_PATHS = [
  { path: '/sign-in', heading: /TenderIQ/i },
  { path: '/', title: /TenderIQ/ },
];

for (const route of PUBLIC_PATHS) {
  test(`public route ${route.path} loads`, async ({ page }) => {
    await page.goto(route.path);
    if ('heading' in route) {
      await expect(page.locator('h1')).toContainText(route.heading);
    } else {
      await expect(page).toHaveTitle(route.title!);
    }
  });
}

test('unauthenticated dashboard redirects to sign-in', async ({ page }) => {
  await page.goto('/dashboard');
  await page.waitForURL(/sign-in/, { timeout: 15000 });
  expect(page.url()).toMatch(/sign-in/);
});
