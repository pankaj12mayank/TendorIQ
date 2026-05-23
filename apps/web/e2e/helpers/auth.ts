import type { Page } from '@playwright/test';

import { tokensFromLoginResponse, userFromLoginResponse } from '../../src/lib/auth-api';

export function apiBaseUrl(): string {
  return (
    process.env.E2E_API_URL ||
    process.env.PLAYWRIGHT_API_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    'http://127.0.0.1:8000'
  ).replace(/\/$/, '');
}

export async function isApiReachable(): Promise<boolean> {
  try {
    const res = await fetch(`${apiBaseUrl()}/health`, { signal: AbortSignal.timeout(3000) });
    return res.ok;
  } catch {
    return false;
  }
}

export async function loginViaApi(email: string, password: string) {
  const res = await fetch(`${apiBaseUrl()}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Login failed (${res.status}): ${body}`);
  }
  return res.json() as Promise<Record<string, unknown>>;
}

export async function seedBrowserSession(page: Page, loginJson: Record<string, unknown>) {
  const tokens = tokensFromLoginResponse(loginJson as Parameters<typeof tokensFromLoginResponse>[0]);
  const user = userFromLoginResponse(loginJson as Parameters<typeof userFromLoginResponse>[0]);
  const expiresInSec = tokens.expires_in ?? 1800;

  await page.goto('/');
  await page.evaluate(
    ({ token, refresh, userJson, expiresIn }) => {
      const expiresAt = Date.now() + expiresIn * 1000;
      localStorage.setItem('tenderiq_auth_token', token);
      localStorage.setItem('tenderiq_auth_user', userJson);
      localStorage.setItem('tenderiq_auth_expires_at', String(expiresAt));
      if (refresh) {
        localStorage.setItem('tenderiq_auth_refresh', refresh);
      }
      document.cookie = `__session=${token}; path=/; max-age=${expiresIn}; SameSite=Lax`;
    },
    {
      token: tokens.access_token,
      refresh: tokens.refresh_token ?? '',
      userJson: JSON.stringify(user),
      expiresIn: expiresInSec,
    }
  );
}

export async function loginAndSaveStorage(
  page: Page,
  opts: { email: string; password: string; storagePath: string }
) {
  const data = await loginViaApi(opts.email, opts.password);
  await seedBrowserSession(page, data);
  await page.context().storageState({ path: opts.storagePath });
}
