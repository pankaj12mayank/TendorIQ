import { test, expect } from '@playwright/test';

test.describe('Password reset routes', () => {
  test('forgot-password page loads', async ({ page }) => {
    await page.goto('/forgot-password');
    await expect(page).toHaveURL(/\/forgot-password/);
    await expect(page.getByText('Forgot password')).toBeVisible();
  });

  test('reset-password page loads', async ({ page }) => {
    await page.goto('/reset-password?token=smoke-test');
    await expect(page).toHaveURL(/\/reset-password/);
  });
});
