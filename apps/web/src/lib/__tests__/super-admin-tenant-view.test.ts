import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';

import {
  activateSuperAdminTenantView,
  clearSuperAdminTenantView,
  isSuperAdminTenantViewActive,
} from '../super-admin-tenant-view';

describe('super-admin-tenant-view', () => {
  beforeEach(() => {
    vi.stubGlobal('window', { location: { search: '' } });
    vi.stubGlobal('sessionStorage', {
      getItem: vi.fn(() => null),
      setItem: vi.fn(),
      removeItem: vi.fn(),
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('activates from session flag', () => {
    activateSuperAdminTenantView();
    vi.mocked(sessionStorage.getItem).mockReturnValue('1');
    expect(isSuperAdminTenantViewActive()).toBe(true);
  });

  it('clears tenant view mode', () => {
    clearSuperAdminTenantView();
    expect(sessionStorage.removeItem).toHaveBeenCalled();
  });
});
