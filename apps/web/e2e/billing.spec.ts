import { test, expect } from '@playwright/test';

test.describe('Billing routes', () => {
  test('billing page or sign-in when unauthenticated', async ({ page }) => {
    await page.goto('/dashboard/billing');
    await expect(page).toHaveURL(/\/(sign-in|dashboard\/billing)/);
  });

  test('usage page or sign-in when unauthenticated', async ({ page }) => {
    await page.goto('/dashboard/usage');
    await expect(page).toHaveURL(/\/(sign-in|dashboard\/usage)/);
  });
});
