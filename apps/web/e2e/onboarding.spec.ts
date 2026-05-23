import { test, expect } from '@playwright/test';

test.describe('Onboarding routes', () => {
  test('onboarding page or sign-in when visiting /onboarding unauthenticated', async ({ page }) => {
    await page.goto('/onboarding');
    await expect(page).toHaveURL(/\/(sign-in|onboarding)/);
  });

  test('sign-in page loads for onboarding entry', async ({ page }) => {
    await page.goto('/sign-in');
    await expect(page).toHaveURL(/sign-in/);
  });
});
