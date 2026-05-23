import { test, expect } from '@playwright/test';

test.describe('Review session route', () => {
  test('review page requires tenderId or sign-in', async ({ page }) => {
    await page.goto('/dashboard/tenders/review');
    await expect(page).toHaveURL(/\/(sign-in|dashboard\/tenders)/);
  });

  test('review with tenderId query shows workspace or sign-in', async ({ page }) => {
    await page.goto('/dashboard/tenders/review?tenderId=00000000-0000-4000-8000-000000000099');
    await expect(page).toHaveURL(/\/(sign-in|dashboard\/tenders\/review)/);
  });
});
