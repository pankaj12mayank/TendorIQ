import { create } from 'zustand';
import { 
  QuotaStatus, 
  QuotaAlert, 
  UsageSummary, 
  AdminQuotaOverride,
  FeatureKey,
  RealTimeUsageUpdate,
  QuotaCheckResult
} from './types';
import { MOCK_QUOTA_STATUS, MOCK_ALERTS, MOCK_USAGE_SUMMARY } from './constants';

interface UsageState {
  quotas: QuotaStatus[];
  alerts: QuotaAlert[];
  usageSummary: UsageSummary | null;
  overrides: AdminQuotaOverride[];
  isLoading: boolean;
  isRealTimeActive: boolean;
  realtimeUpdates: RealTimeUsageUpdate[];

  setQuotas: (quotas: QuotaStatus[]) => void;
  setAlerts: (alerts: QuotaAlert[]) => void;
  setUsageSummary: (summary: UsageSummary) => void;
  setOverrides: (overrides: AdminQuotaOverride[]) => void;
  setLoading: (loading: boolean) => void;

  incrementUsage: (featureKey: FeatureKey, amount: number) => void;
  decrementUsage: (featureKey: FeatureKey, amount: number) => void;
  
  markAlertRead: (alertId: string) => void;
  dismissAlert: (alertId: string) => void;
  clearAllAlerts: () => void;
  
  addOverride: (override: AdminQuotaOverride) => void;
  revokeOverride: (overrideId: string) => void;
  
  checkQuota: (featureKey: FeatureKey, required?: number) => QuotaCheckResult;
  
  addRealtimeUpdate: (update: RealTimeUsageUpdate) => void;
  clearRealtimeUpdates: () => void;
  toggleRealTime: (active: boolean) => void;
  
  refreshUsage: () => Promise<void>;
  refreshAlerts: () => Promise<void>;
}

export const useUsageStore = create<UsageState>((set, get) => ({
  quotas: MOCK_QUOTA_STATUS,
  alerts: MOCK_ALERTS,
  usageSummary: MOCK_USAGE_SUMMARY,
  overrides: [],
  isLoading: false,
  isRealTimeActive: false,
  realtimeUpdates: [],

  setQuotas: (quotas) => set({ quotas }),
  setAlerts: (alerts) => set({ alerts }),
  setUsageSummary: (summary) => set({ usageSummary: summary }),
  setOverrides: (overrides) => set({ overrides }),
  setLoading: (loading) => set({ isLoading: loading }),

  incrementUsage: (featureKey, amount) => {
    set((state) => ({
      quotas: state.quotas.map((q) =>
        q.featureKey === featureKey
          ? {
              ...q,
              used: q.used + amount,
              remaining: q.remaining !== null ? Math.max(0, q.remaining - amount) : null,
              percentage: q.limit ? Math.min(100, ((q.used + amount) / q.limit) * 100) : q.percentage,
              isExceeded: q.limit ? q.used + amount >= q.limit : false,
              alertLevel: q.limit ? getAlertLevelFromPercentage(((q.used + amount) / q.limit) * 100) : q.alertLevel,
            }
          : q
      ),
    }));

    const quota = get().quotas.find((q) => q.featureKey === featureKey);
    if (quota && quota.alertLevel) {
      const newAlert: QuotaAlert = {
        id: `alert-${Date.now()}`,
        userId: 'user-123',
        featureKey,
        alertType: quota.alertLevel,
        thresholdPercent: quota.percentage,
        currentPercent: quota.percentage,
        isRead: false,
        isDismissed: false,
        createdAt: new Date().toISOString(),
      };
      set((state) => ({ alerts: [newAlert, ...state.alerts] }));
    }
  },

  decrementUsage: (featureKey, amount) => {
    set((state) => ({
      quotas: state.quotas.map((q) =>
        q.featureKey === featureKey
          ? {
              ...q,
              used: Math.max(0, q.used - amount),
              remaining: q.remaining !== null ? q.remaining + amount : null,
              percentage: q.limit ? Math.max(0, ((q.used - amount) / q.limit) * 100) : q.percentage,
            }
          : q
      ),
    }));
  },

  markAlertRead: (alertId) => {
    set((state) => ({
      alerts: state.alerts.map((a) =>
        a.id === alertId ? { ...a, isRead: true, readAt: new Date().toISOString() } : a
      ),
    }));
  },

  dismissAlert: (alertId) => {
    set((state) => ({
      alerts: state.alerts.map((a) =>
        a.id === alertId ? { ...a, isDismissed: true } : a
      ),
    }));
  },

  clearAllAlerts: () => set({ alerts: [] }),

  addOverride: (override) => {
    set((state) => ({ overrides: [...state.overrides, override] }));
  },

  revokeOverride: (overrideId) => {
    set((state) => ({
      overrides: state.overrides.map((o) =>
        o.id === overrideId ? { ...o, isActive: false, revokedAt: new Date().toISOString() } : o
      ),
    }));
  },

  checkQuota: (featureKey, required = 1) => {
    const quota = get().quotas.find((q) => q.featureKey === featureKey);
    const override = get().overrides.find(
      (o) => o.featureKey === featureKey && o.isActive && (!o.expiresAt || new Date(o.expiresAt) > new Date())
    );

    const limit = override?.newLimit ?? quota?.limit ?? null;
    const remaining = limit !== null && quota ? Math.max(0, limit - quota.used) : null;
    const percentage = limit ? (quota?.used ?? 0) / limit * 100 : 0;

    return {
      allowed: remaining === null || remaining >= required,
      currentUsage: quota?.used ?? 0,
      limit,
      remaining,
      percentage,
      required,
      exceeded: remaining !== null && remaining < required,
      upgradeRequired: remaining !== null && remaining < required,
      suggestedPlan: percentage > 90 ? 'enterprise' : percentage > 70 ? 'pro' : undefined,
    };
  },

  addRealtimeUpdate: (update) => {
    set((state) => ({
      realtimeUpdates: [update, ...state.realtimeUpdates].slice(0, 50),
      quotas: state.quotas.map((q) =>
        q.featureKey === update.featureKey
          ? { ...q, used: update.newTotal }
          : q
      ),
    }));
  },

  clearRealtimeUpdates: () => set({ realtimeUpdates: [] }),
  toggleRealTime: (active) => set({ isRealTimeActive: active }),

  refreshUsage: async () => {
    set({ isLoading: true });
    await new Promise((resolve) => setTimeout(resolve, 800));
    set({ isLoading: false });
  },

  refreshAlerts: async () => {
    set({ isLoading: true });
    await new Promise((resolve) => setTimeout(resolve, 500));
    set({ isLoading: false });
  },
}));

function getAlertLevelFromPercentage(percentage: number): 'warning' | 'critical' | 'exceeded' | undefined {
  if (percentage >= 100) return 'exceeded';
  if (percentage >= 85) return 'critical';
  if (percentage >= 70) return 'warning';
  return undefined;
}

export default useUsageStore;