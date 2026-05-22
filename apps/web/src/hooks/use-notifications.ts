import { useState, useCallback, useEffect } from 'react';
import { api } from '@/lib/api-client';
import { parseNotificationsList } from '@/lib/notifications-api';
import { useNotificationStore, Notification } from '@/components/notifications/store';

interface UseNotificationsReturn {
  notifications: Notification[];
  unreadCount: number;
  isLoading: boolean;
  fetchNotifications: () => Promise<void>;
  markAsRead: (id: string) => Promise<void>;
  markAllAsRead: () => Promise<void>;
  removeNotification: (id: string) => Promise<void>;
  addNotification: (notification: Omit<Notification, 'id' | 'createdAt'>) => void;
}

export function useNotifications(): UseNotificationsReturn {
  const {
    notifications,
    unreadCount,
    isLoading,
    setNotifications,
    addNotification: storeAddNotification,
    markAsRead: storeMarkAsRead,
    markAllAsRead: storeMarkAllAsRead,
    removeNotification: storeRemoveNotification,
    setLoading,
  } = useNotificationStore();

  const [, setError] = useState<string | null>(null);

  const fetchNotifications = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const res = await api.get<unknown>('/api/v1/notifications/');
      setNotifications(parseNotificationsList(res));
    } catch {
      setError('Failed to fetch notifications');
    } finally {
      setLoading(false);
    }
  }, [setNotifications, setLoading]);

  const markAsRead = useCallback(
    async (id: string) => {
      try {
        await api.patch(`/api/v1/notifications/${id}/read`);
        storeMarkAsRead(id);
      } catch {
        setError('Failed to mark notification as read');
      }
    },
    [storeMarkAsRead]
  );

  const markAllAsRead = useCallback(async () => {
    try {
      await api.post('/api/v1/notifications/read-all');
      storeMarkAllAsRead();
    } catch {
      setError('Failed to mark all as read');
    }
  }, [storeMarkAllAsRead]);

  const removeNotification = useCallback(
    async (id: string) => {
      try {
        await api.delete(`/api/v1/notifications/${id}`);
        storeRemoveNotification(id);
      } catch {
        setError('Failed to remove notification');
      }
    },
    [storeRemoveNotification]
  );

  const addNotification = useCallback(
    (notification: Omit<Notification, 'id' | 'createdAt'>) => {
      storeAddNotification({
        ...notification,
        id: `notif-${crypto.randomUUID?.() ?? Date.now()}`,
        createdAt: new Date().toISOString(),
      });
    },
    [storeAddNotification]
  );

  useEffect(() => {
    void fetchNotifications();
  }, [fetchNotifications]);

  return {
    notifications,
    unreadCount,
    isLoading,
    fetchNotifications,
    markAsRead,
    markAllAsRead,
    removeNotification,
    addNotification,
  };
}

interface UseEmailTriggersReturn {
  triggerUploadReceived: (data: {
    user_email: string;
    file_name: string;
    tender_name: string;
  }) => Promise<void>;
  triggerProcessingCompleted: (data: {
    user_email: string;
    file_name: string;
    tender_name: string;
  }) => Promise<void>;
  triggerProcessingFailed: (data: {
    user_email: string;
    file_name: string;
    error: string;
  }) => Promise<void>;
  triggerQuotaExceeded: (data: {
    user_email: string;
    feature: string;
    used: number;
    limit: number;
  }) => Promise<void>;
  triggerSubscriptionAlert: (data: {
    user_email: string;
    alert_type: string;
    message: string;
  }) => Promise<void>;
}

export function useEmailTriggers(): UseEmailTriggersReturn {
  const postTrigger = useCallback(async (path: string, data: Record<string, unknown>) => {
    await api.post(`/api/v1/email/triggers/${path}`, data);
  }, []);

  const triggerUploadReceived = useCallback(
    async (data: { user_email: string; file_name: string; tender_name: string }) => {
      await postTrigger('upload-received', data);
    },
    [postTrigger]
  );

  const triggerProcessingCompleted = useCallback(
    async (data: { user_email: string; file_name: string; tender_name: string }) => {
      await postTrigger('processing-completed', data);
    },
    [postTrigger]
  );

  const triggerProcessingFailed = useCallback(
    async (data: { user_email: string; file_name: string; error: string }) => {
      await postTrigger('processing-failed', data);
    },
    [postTrigger]
  );

  const triggerQuotaExceeded = useCallback(
    async (data: { user_email: string; feature: string; used: number; limit: number }) => {
      await postTrigger('quota-exceeded', data);
    },
    [postTrigger]
  );

  const triggerSubscriptionAlert = useCallback(
    async (data: { user_email: string; alert_type: string; message: string }) => {
      await postTrigger('subscription-alert', data);
    },
    [postTrigger]
  );

  return {
    triggerUploadReceived,
    triggerProcessingCompleted,
    triggerProcessingFailed,
    triggerQuotaExceeded,
    triggerSubscriptionAlert,
  };
}
