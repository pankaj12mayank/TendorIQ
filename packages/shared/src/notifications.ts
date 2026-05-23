/**
 * Notification API row ↔ UI store shape (snake_case / camelCase tolerant).
 */

export type NotificationUiType = 'info' | 'success' | 'warning' | 'error';

export interface NotificationUi {
  id: string;
  title: string;
  message: string;
  type: NotificationUiType;
  isRead: boolean;
  createdAt: string;
  actionUrl?: string;
  actionLabel?: string;
}

export interface ApiNotificationRow {
  id: string;
  type?: string;
  title: string;
  message: string;
  is_read?: boolean;
  isRead?: boolean;
  created_at?: string;
  createdAt?: string;
  data?: Record<string, unknown>;
}

const UI_TYPES: NotificationUiType[] = ['info', 'success', 'warning', 'error'];

function mapNotificationType(raw: string | undefined): NotificationUiType {
  if (raw && UI_TYPES.includes(raw as NotificationUiType)) {
    return raw as NotificationUiType;
  }
  if (raw === 'alert') return 'warning';
  return 'info';
}

export function mapApiNotification(row: ApiNotificationRow): NotificationUi {
  const data = row.data ?? {};
  const actionUrl =
    (typeof data.actionUrl === 'string' && data.actionUrl) ||
    (typeof data.action_url === 'string' && data.action_url) ||
    undefined;
  const actionLabel =
    (typeof data.actionLabel === 'string' && data.actionLabel) ||
    (typeof data.action_label === 'string' && data.action_label) ||
    undefined;

  return {
    id: row.id,
    title: row.title,
    message: row.message,
    type: mapNotificationType(row.type),
    isRead: Boolean(row.isRead ?? row.is_read),
    createdAt: row.createdAt ?? row.created_at ?? new Date().toISOString(),
    actionUrl,
    actionLabel,
  };
}
