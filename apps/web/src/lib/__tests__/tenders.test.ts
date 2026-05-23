import { describe, expect, it } from 'vitest';

import { mapTenderFromApi } from '@tendoriq/shared/tenders';
import { isAppFeatureEnabled } from '../feature-flags';

describe('@tendoriq/shared tenders', () => {
  it('maps tenant_id to tenantId and legacy organizationId', () => {
    const t = mapTenderFromApi({
      id: '1',
      title: 'A',
      status: 'draft',
      tenant_id: '00000000-0000-4000-8000-000000000001',
    });
    expect(t.tenantId).toBe('00000000-0000-4000-8000-000000000001');
    expect(t.organizationId).toBe(t.tenantId);
  });
});

describe('feature-flags', () => {
  it('defaults advanced analytics off when env unset', () => {
    expect(isAppFeatureEnabled('advanced_analytics')).toBe(false);
  });
});
