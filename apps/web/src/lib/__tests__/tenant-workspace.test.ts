import { describe, expect, it } from 'vitest';

import { hasTenantWorkspace, TENANT_WORKSPACE_REQUIRED } from '../tenant-workspace';

describe('tenant-workspace', () => {
  it('requires tenantId on user', () => {
    expect(hasTenantWorkspace(null)).toBe(false);
    expect(hasTenantWorkspace({ tenantId: '' } as never)).toBe(false);
    expect(hasTenantWorkspace({ tenantId: 't-1' } as never)).toBe(true);
  });

  it('exposes stable workspace message', () => {
    expect(TENANT_WORKSPACE_REQUIRED).toMatch(/workspace/i);
  });
});
