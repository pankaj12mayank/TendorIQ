import { test as setup } from '@playwright/test';

import { isApiReachable, loginAndSaveStorage } from './helpers/auth';

setup('authenticate super admin', async ({ page }) => {
  if (!(await isApiReachable())) {
    setup.skip(true, 'API not reachable — start run.bat or set E2E_API_URL');
  }

  await loginAndSaveStorage(page, {
    email: process.env.E2E_ADMIN_EMAIL || 'admin@tendoriq.com',
    password: process.env.E2E_ADMIN_PASSWORD || 'SuperAdmin@123',
    storagePath: 'e2e/.auth/admin.json',
  });
});
