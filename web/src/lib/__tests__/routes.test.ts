import { describe, expect, it } from 'vitest';

import {
  isLiteDashboardPath,
  isPublicAppPath,
  resolveLegacyDashboardRedirect,
  ROUTES,
} from '../routes';

describe('routes', () => {
  it('defines canonical Lite MVP paths', () => {
    expect(ROUTES.dashboard).toBe('/dashboard');
    expect(ROUTES.upload).toBe('/dashboard/upload');
    expect(ROUTES.settings).toBe('/dashboard/settings');
  });

  it('treats marketing and auth paths as public', () => {
    expect(isPublicAppPath('/')).toBe(true);
    expect(isPublicAppPath('/sign-in')).toBe(true);
    expect(isPublicAppPath('/sign-up')).toBe(true);
    expect(isPublicAppPath('/dashboard')).toBe(false);
  });

  it('recognizes lite dashboard paths', () => {
    expect(isLiteDashboardPath('/dashboard/upload')).toBe(true);
    expect(isLiteDashboardPath('/dashboard/settings')).toBe(true);
    expect(isLiteDashboardPath('/dashboard/billing')).toBe(false);
  });

  it('redirects legacy billing and settings sub-routes', () => {
    expect(resolveLegacyDashboardRedirect('/dashboard/billing')).toBe(
      '/dashboard/settings?tab=billing'
    );
    expect(resolveLegacyDashboardRedirect('/dashboard/settings/ai')).toBe(
      '/dashboard/settings?tab=ai'
    );
    expect(resolveLegacyDashboardRedirect('/dashboard/tenders')).toBe(ROUTES.upload);
  });
});
