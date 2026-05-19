import { useState, useCallback, useEffect } from 'react';
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
    setLoading
  } = useNotificationStore();
  
  const [error, setError] = useState<string | null>(null);

  const fetchNotifications = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      await new Promise(resolve => setTimeout(resolve, 500));
      
      const mockNotifications: Notification[] = [
        {
          id: '1',
          title: 'File Processing Complete',
          message: 'Your uploaded tender document has been processed successfully.',
          type: 'success',
          isRead: false,
          createdAt: new Date(Date.now() - 30 * 60000).toISOString(),
          actionUrl: '/dashboard/tenders/analysis',
          actionLabel: 'View Results'
        },
        {
          id: '2',
          title: 'Quota Warning',
          message: 'You have used 80% of your AI analysis quota.',
          type: 'warning',
          isRead: false,
          createdAt: new Date(Date.now() - 2 * 3600000).toISOString(),
          actionUrl: '/dashboard/billing',
          actionLabel: 'Upgrade'
        },
        {
          id: '3',
          title: 'New Tender Available',
          message: 'A new tender matching your preferences is available.',
          type: 'info',
          isRead: true,
          createdAt: new Date(Date.now() - 24 * 3600000).toISOString(),
        }
      ];
      
      setNotifications(mockNotifications);
    } catch (err) {
      setError('Failed to fetch notifications');
    } finally {
      setLoading(false);
    }
  }, [setNotifications, setLoading]);

  const markAsRead = useCallback(async (id: string) => {
    storeMarkAsRead(id);
  }, [storeMarkAsRead]);

  const markAllAsRead = useCallback(async () => {
    storeMarkAllAsRead();
  }, [storeMarkAllAsRead]);

  const removeNotification = useCallback(async (id: string) => {
    storeRemoveNotification(id);
  }, [storeRemoveNotification]);

  const addNotification = useCallback((notification: Omit<Notification, 'id' | 'createdAt'>) => {
    storeAddNotification({
      ...notification,
      id: `notif-${Date.now()}`,
      createdAt: new Date().toISOString()
    });
  }, [storeAddNotification]);

  useEffect(() => {
    fetchNotifications();
  }, []);

  return {
    notifications,
    unreadCount,
    isLoading,
    fetchNotifications,
    markAsRead,
    markAllAsRead,
    removeNotification,
    addNotification
  };
}

interface UseEmailTriggersReturn {
  triggerUploadReceived: (data: { user_email: string; file_name: string; tender_name: string }) => Promise<void>;
  triggerProcessingCompleted: (data: { user_email: string; file_name: string; tender_name: string }) => Promise<void>;
  triggerProcessingFailed: (data: { user_email: string; file_name: string; error: string }) => Promise<void>;
  triggerQuotaExceeded: (data: { user_email: string; feature: string; used: number; limit: number }) => Promise<void>;
  triggerSubscriptionAlert: (data: { user_email: string; alert_type: string; message: string }) => Promise<void>;
}

export function useEmailTriggers(): UseEmailTriggersReturn {
  const [isLoading, setIsLoading] = useState(false);

  const triggerUploadReceived = useCallback(async (data) => {
    setIsLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 500));
      console.log('Upload received email triggered:', data);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const triggerProcessingCompleted = useCallback(async (data) => {
    setIsLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 500));
      console.log('Processing completed email triggered:', data);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const triggerProcessingFailed = useCallback(async (data) => {
    setIsLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 500));
      console.log('Processing failed email triggered:', data);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const triggerQuotaExceeded = useCallback(async (data) => {
    setIsLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 500));
      console.log('Quota exceeded email triggered:', data);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const triggerSubscriptionAlert = useCallback(async (data) => {
    setIsLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 500));
      console.log('Subscription alert email triggered:', data);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    triggerUploadReceived,
    triggerProcessingCompleted,
    triggerProcessingFailed,
    triggerQuotaExceeded,
    triggerSubscriptionAlert
  };
}