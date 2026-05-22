import { create } from 'zustand';

export interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  isRead: boolean;
  createdAt: string;
  actionUrl?: string;
  actionLabel?: string;
}

interface NotificationState {
  notifications: Notification[];
  isLoading: boolean;
  unreadCount: number;
  
  setNotifications: (notifications: Notification[]) => void;
  addNotification: (notification: Notification) => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  removeNotification: (id: string) => void;
  clearAll: () => void;
  setLoading: (loading: boolean) => void;
}

export const useNotificationStore = create<NotificationState>((set, get) => ({
  notifications: [],
  isLoading: false,
  unreadCount: 0,

  setNotifications: (notifications) => set({ 
    notifications,
    unreadCount: notifications.filter(n => !n.isRead).length
  }),

  addNotification: (notification) => set((state) => ({
    notifications: [notification, ...state.notifications],
    unreadCount: state.unreadCount + (notification.isRead ? 0 : 1)
  })),

  markAsRead: (id) => set((state) => ({
    notifications: state.notifications.map(n => 
      n.id === id ? { ...n, isRead: true } : n
    ),
    unreadCount: Math.max(0, state.unreadCount - 1)
  })),

  markAllAsRead: () => set((state) => ({
    notifications: state.notifications.map(n => ({ ...n, isRead: true })),
    unreadCount: 0
  })),

  removeNotification: (id) => set((state) => {
    const notification = state.notifications.find(n => n.id === id);
    return {
      notifications: state.notifications.filter(n => n.id !== id),
      unreadCount: state.unreadCount - (notification && !notification.isRead ? 1 : 0)
    };
  }),

  clearAll: () => set({ notifications: [], unreadCount: 0 }),
  
  setLoading: (loading) => set({ isLoading: loading })
}));

export const selectUnreadNotifications = (state: NotificationState) => 
  state.notifications.filter(n => !n.isRead);

export const selectRecentNotifications = (state: NotificationState, limit = 5) => 
  state.notifications.slice(0, limit);