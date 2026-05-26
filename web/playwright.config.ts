import { defineConfig, devices } from '@playwright/test';

const baseURL = process.env.BASE_URL || process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL,
    trace: 'on-first-retry',
  },
  projects: [
    { name: 'setup-demo', testMatch: /auth-demo\.setup\.ts/ },
    { name: 'setup-admin', testMatch: /auth-admin\.setup\.ts/ },
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
      testIgnore: [/\.setup\.ts$/, /authenticated-flows\.spec\.ts/],
    },
    {
      name: 'chromium-authenticated',
      dependencies: ['setup-demo', 'setup-admin'],
      testMatch: /authenticated-flows\.spec\.ts/,
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
