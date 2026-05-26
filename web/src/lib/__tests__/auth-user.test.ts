import { describe, expect, it } from 'vitest';

import type { AuthUser } from '../auth-session';
import { buildApiAuthHeaders, getMembershipRole } from '../auth-user';

describe('getMembershipRole', () => {
  it('prefers membershipRole over display role', () => {
    const user: AuthUser = {
      id: '1',
      email: 'a@b.com',
      name: 'A',
      role: 'admin',
      membershipRole: 'viewer',
    };
    expect(getMembershipRole(user)).toBe('viewer');
  });

  it('returns super_admin for platform role', () => {
    const user: AuthUser = {
      id: '1',
      email: 'a@b.com',
      name: 'A',
      role: 'super_admin',
    };
    expect(getMembershipRole(user)).toBe('super_admin');
  });
});

describe('buildApiAuthHeaders', () => {
  it('includes Authorization and X-Tenant-ID when present', () => {
    const headers = buildApiAuthHeaders('tok', {
      id: '1',
      email: 'a@b.com',
      name: 'A',
      tenantId: 'tenant-uuid',
    });
    expect(headers).toMatchObject({
      Authorization: 'Bearer tok',
      'X-Tenant-ID': 'tenant-uuid',
    });
  });
});
