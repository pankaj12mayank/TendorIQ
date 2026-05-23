import { test, expect } from '@playwright/test';

test.describe('Documents & upload routes', () => {
  test('documents page or sign-in when unauthenticated', async ({ page }) => {
    await page.goto('/dashboard/documents');
    await expect(page).toHaveURL(/\/(sign-in|dashboard\/documents)/);
  });

  test('upload page or sign-in when unauthenticated', async ({ page }) => {
    await page.goto('/dashboard/upload');
    await expect(page).toHaveURL(/\/(sign-in|dashboard\/upload)/);
  });
});
