import { create } from 'zustand';

export interface DashboardNotification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  time: string;
  read: boolean;
}

export interface DashboardActivity {
  id: string;
  type: 'upload' | 'process' | 'complete' | 'error';
  title: string;
  description?: string;
  time: string;
}

export interface DashboardStat {
  title: string;
  value: string;
  trend: string;
  trendDirection: 'up' | 'down' | 'neutral';
}

interface DashboardState {
  notifications: DashboardNotification[];
  activities: DashboardActivity[];
  stats: DashboardStat[];
  isLoading: boolean;
  setNotifications: (notifications: DashboardNotification[]) => void;
  markNotificationRead: (id: string) => void;
  markAllNotificationsRead: () => void;
  addActivity: (activity: DashboardActivity) => void;
  setStats: (stats: DashboardStat[]) => void;
  setLoading: (loading: boolean) => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  notifications: [],
  activities: [],
  stats: [],
  isLoading: false,

  setNotifications: (notifications) => set({ notifications }),

  markNotificationRead: (id) =>
    set((state) => ({
      notifications: state.notifications.map((n) =>
        n.id === id ? { ...n, read: true } : n
      ),
    })),

  markAllNotificationsRead: () =>
    set((state) => ({
      notifications: state.notifications.map((n) => ({ ...n, read: true })),
    })),

  addActivity: (activity) =>
    set((state) => ({
      activities: [activity, ...state.activities].slice(0, 50),
    })),

  setStats: (stats) => set({ stats }),

  setLoading: (isLoading) => set({ isLoading }),
}));