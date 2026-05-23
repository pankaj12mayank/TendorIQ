import { test, expect } from '@playwright/test';

test.describe('Tenant dashboard core routes', () => {
  test('bids page or sign-in when unauthenticated', async ({ page }) => {
    await page.goto('/dashboard/bids');
    await expect(page).toHaveURL(/\/(sign-in|dashboard\/bids)/);
  });

  test('tenders list or sign-in when unauthenticated', async ({ page }) => {
    await page.goto('/dashboard/tenders');
    await expect(page).toHaveURL(/\/(sign-in|dashboard\/tenders)/);
  });

  test('analytics page or sign-in when unauthenticated', async ({ page }) => {
    await page.goto('/dashboard/analytics');
    await expect(page).toHaveURL(/\/(sign-in|dashboard\/analytics)/);
  });
});
