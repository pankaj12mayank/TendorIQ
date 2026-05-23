import { test, expect } from '@playwright/test';

test.describe('Super admin console', () => {
  test('admin console or sign-in when unauthenticated', async ({ page }) => {
    await page.goto('/dashboard/admin');
    await expect(page).toHaveURL(/\/(sign-in|dashboard\/admin)/);
  });

  test('legacy admin login redirects to sign-in', async ({ page }) => {
    await page.goto('/admin/login');
    await expect(page).toHaveURL(/\/sign-in/);
  });

  test('queue module route resolves', async ({ page }) => {
    await page.goto('/dashboard/admin?module=queue');
    await expect(page).toHaveURL(/\/(sign-in|dashboard\/admin)/);
  });
});
