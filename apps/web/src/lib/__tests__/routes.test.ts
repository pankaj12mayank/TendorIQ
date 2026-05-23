import { describe, expect, it } from 'vitest';

import { isPublicAppPath, ROUTES } from '../routes';

describe('routes', () => {
  it('defines canonical tender and review paths', () => {
    expect(ROUTES.tenderNew).toBe('/dashboard/tenders/new');
    expect(ROUTES.tenderReview).toBe('/dashboard/tenders/review');
    expect(ROUTES.reviewLegacy).toBe('/dashboard/review');
  });

  it('treats marketing and auth paths as public', () => {
    expect(isPublicAppPath('/')).toBe(true);
    expect(isPublicAppPath('/landing')).toBe(true);
    expect(isPublicAppPath('/sign-in')).toBe(true);
    expect(isPublicAppPath('/admin/sign-in')).toBe(true);
    expect(isPublicAppPath('/dashboard')).toBe(false);
  });
});
