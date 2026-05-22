import { describe, expect, it } from 'vitest';

import { mapApiNotification, parseNotificationsList } from '../notifications-api';

describe('notifications-api', () => {
  it('maps snake_case API rows to UI notifications', () => {
    const row = mapApiNotification({
      id: 'n1',
      type: 'success',
      title: 'Done',
      message: 'File processed',
      is_read: false,
      created_at: '2026-01-01T00:00:00Z',
      data: { action_url: '/dashboard', action_label: 'Open' },
    });
    expect(row.isRead).toBe(false);
    expect(row.createdAt).toBe('2026-01-01T00:00:00Z');
    expect(row.actionUrl).toBe('/dashboard');
    expect(row.actionLabel).toBe('Open');
  });

  it('unwraps success/data notification list envelope', () => {
    const list = parseNotificationsList({
      success: true,
      data: [
        {
          id: 'n2',
          title: 'Hi',
          message: 'There',
          type: 'info',
          is_read: true,
          created_at: '2026-01-02T00:00:00Z',
        },
      ],
    });
    expect(list).toHaveLength(1);
    expect(list[0].isRead).toBe(true);
  });
});
