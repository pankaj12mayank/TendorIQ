import { test as setup } from '@playwright/test';

import { isApiReachable, loginAndSaveStorage } from './helpers/auth';

setup('authenticate demo tenant', async ({ page }) => {
  if (!(await isApiReachable())) {
    setup.skip(true, 'API not reachable — start run.bat or set E2E_API_URL');
  }

  await loginAndSaveStorage(page, {
    email: process.env.E2E_DEMO_EMAIL || 'demo@tendoriq.com',
    password: process.env.E2E_DEMO_PASSWORD || 'Demo@123',
    storagePath: 'e2e/.auth/demo.json',
  });
});
