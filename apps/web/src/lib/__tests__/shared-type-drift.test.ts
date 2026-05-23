import { describe, expect, it } from 'vitest';

import { normalizePlanId, normalizeBillingCycle } from '@tendoriq/shared/plans';
import { ADMIN_CONSOLE_ROLES, normalizeDisplayRole } from '@tendoriq/shared/roles';
import { mapApiNotification } from '@tendoriq/shared/notifications';

describe('shared type drift guards', () => {
  it('normalizes plan aliases', () => {
    expect(normalizePlanId('plan_pro')).toBe('professional');
    expect(normalizeBillingCycle('annual')).toBe('yearly');
  });

  it('includes owner and member in admin console roles', () => {
    expect(ADMIN_CONSOLE_ROLES).toContain('owner');
    expect(ADMIN_CONSOLE_ROLES).toContain('member');
  });

  it('normalizes tenant_admin to admin', () => {
    expect(normalizeDisplayRole('tenant_admin')).toBe('admin');
  });

  it('maps notification snake_case fields', () => {
    const n = mapApiNotification({
      id: '1',
      title: 'T',
      message: 'M',
      is_read: true,
      created_at: '2026-01-01T00:00:00Z',
      data: { action_url: '/x', action_label: 'Go' },
    });
    expect(n.isRead).toBe(true);
    expect(n.actionUrl).toBe('/x');
    expect(n.actionLabel).toBe('Go');
  });
});
