import { test, expect } from '@playwright/test';

/**
 * Authenticated E2E — requires API (:8000) and web (:3000).
 * Setup projects seed storage from POST /api/v1/auth/login.
 */
test.describe('Authenticated tenant @authenticated', () => {
  test.use({ storageState: 'e2e/.auth/demo.json' });

  test('sign-in session reaches tenders list', async ({ page }) => {
    await page.goto('/dashboard/tenders');
    await expect(page).toHaveURL(/\/dashboard\/tenders/);
    await expect(page.locator('body')).not.toContainText('Sign in to TenderIQ');
  });

  test('upload page loads for tenant', async ({ page }) => {
    await page.goto('/dashboard/upload');
    await expect(page).toHaveURL(/\/dashboard\/upload/);
  });

  test('review page accepts tenderId query', async ({ page }) => {
    await page.goto('/dashboard/tenders/review?tenderId=00000000-0000-0000-0000-000000000001');
    await expect(page).toHaveURL(/\/dashboard\/tenders\/review/);
  });
});

test.describe('Authenticated super admin @authenticated', () => {
  test.use({ storageState: 'e2e/.auth/admin.json' });

  test('admin console users module', async ({ page }) => {
    await page.goto('/dashboard/admin?module=users');
    await expect(page).toHaveURL(/\/dashboard\/admin/);
    await expect(page.getByRole('heading', { name: 'User Management' })).toBeVisible({ timeout: 15000 });
  });

  test('admin queue module', async ({ page }) => {
    await page.goto('/dashboard/admin?module=queue');
    await expect(page).toHaveURL(/\/dashboard\/admin/);
  });
});
