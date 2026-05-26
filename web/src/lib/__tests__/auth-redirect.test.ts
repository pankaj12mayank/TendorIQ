import { describe, expect, it } from 'vitest';

import { getPostLoginPath } from '../auth-redirect';

describe('getPostLoginPath', () => {
  it('sends super_admin to platform console', () => {
    expect(getPostLoginPath('super_admin')).toBe('/dashboard/admin');
  });

  it('sends tenant membership roles to dashboard', () => {
    for (const role of ['owner', 'admin', 'manager', 'analyst', 'member', 'viewer']) {
      expect(getPostLoginPath(role)).toBe('/dashboard');
    }
  });

  it('sends unknown roles to dashboard in Lite MVP', () => {
    expect(getPostLoginPath(undefined)).toBe('/dashboard');
    expect(getPostLoginPath('user')).toBe('/dashboard');
  });
});
