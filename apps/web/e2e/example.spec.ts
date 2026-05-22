import { test, expect } from '@playwright/test';

test('homepage loads', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/TenderIQ/);
});

test('sign-in page accessible', async ({ page }) => {
  await page.goto('/sign-in');
  await expect(page.locator('h1')).toContainText(/sign in/i);
});
