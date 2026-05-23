import type { Notification } from '@/components/notifications/store';
import {
  mapApiNotification,
  type ApiNotificationRow,
  type NotificationUi,
} from '@tendoriq/shared/notifications';
import { parsePaginated, unwrapData } from './api-envelope';

export type { ApiNotificationRow, NotificationUi };

export { mapApiNotification };

export function parseNotificationsList(payload: unknown): Notification[] {
  const page = parsePaginated<ApiNotificationRow>(payload as { data?: ApiNotificationRow[] });
  const rows = page.data.length ? page.data : unwrapData<ApiNotificationRow[]>(payload) ?? [];
  const list = Array.isArray(rows) ? rows : [];
  return list.map(mapApiNotification) as Notification[];
}
