import type { Notification } from '@/components/notifications/store';
import { unwrapData } from './api-envelope';

const UI_TYPES = ['info', 'success', 'warning', 'error'] as const;

type UiType = (typeof UI_TYPES)[number];

function mapNotificationType(raw: string | undefined): UiType {
  if (raw && (UI_TYPES as readonly string[]).includes(raw)) {
    return raw as UiType;
  }
  if (raw === 'alert') return 'warning';
  return 'info';
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

export function mapApiNotification(row: ApiNotificationRow): Notification {
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

export function parseNotificationsList(payload: unknown): Notification[] {
  const rows = unwrapData<ApiNotificationRow[]>(payload as { data?: ApiNotificationRow[] });
  const list = Array.isArray(rows) ? rows : [];
  return list.map(mapApiNotification);
}
