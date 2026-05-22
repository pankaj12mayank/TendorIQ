import { useCallback, useState } from 'react';
import { useUsageStore } from '@/components/usage/store';
import { 
  QuotaStatus, 
  QuotaAlert, 
  UsageSummary, 
  AdminQuotaOverride,
  FeatureKey,
  RealTimeUsageUpdate,
  QuotaCheckResult,
  OverrideRequest
} from '@/components/usage/types';
import { api } from '@/lib/api-client';
import { mapUsageQuotas, mapUsageSummary } from '@/lib/billing-api';

interface UseUsageApiReturn {
  quotas: QuotaStatus[];
  alerts: QuotaAlert[];
  usageSummary: UsageSummary | null;
  overrides: AdminQuotaOverride[];
  isLoading: boolean;
  realtimeUpdates: RealTimeUsageUpdate[];
  
  fetchQuotas: () => Promise<QuotaStatus[]>;
  fetchAlerts: () => Promise<QuotaAlert[]>;
  fetchUsageSummary: () => Promise<UsageSummary>;
  fetchOverrides: () => Promise<AdminQuotaOverride[]>;
  
  trackUsage: (featureKey: FeatureKey, quantity: number, metadata?: Record<string, unknown>) => Promise<void>;
  getQuotaStatus: (featureKey: FeatureKey) => QuotaStatus | undefined;
  checkQuota: (featureKey: FeatureKey, required?: number) => QuotaCheckResult;
  
  markAlertRead: (alertId: string) => Promise<void>;
  dismissAlert: (alertId: string) => Promise<void>;
  clearAllAlerts: () => Promise<void>;
  
  subscribeToRealtime: () => () => void;
  
  getAllQuotas: () => QuotaStatus[];
  getActiveAlerts: () => QuotaAlert[];
  getUsageByCategory: () => Record<string, QuotaStatus[]>;
}

export function useUsageApi(): UseUsageApiReturn {
  const store = useUsageStore();
  const [isLoading, setLoading] = useState(false);

  const fetchQuotas = useCallback(async (): Promise<QuotaStatus[]> => {
    setLoading(true);
    try {
      const res = await api.get<{ quotas: QuotaStatus[]; quota?: QuotaStatus[] }>(
        '/api/v1/billing/quota'
      );
      const quotas = mapUsageQuotas(res);
      store.setQuotas(quotas);
      setLoading(false);
      return quotas;
    } catch {
      setLoading(false);
      return [];
    }
  }, []);

  const fetchAlerts = useCallback(async (): Promise<QuotaAlert[]> => {
    setLoading(true);
    try {
      const res = await api.get<{ alerts: QuotaAlert[] }>('/api/v1/notifications?type=quota');
      store.setAlerts(res.alerts);
      setLoading(false);
      return res.alerts;
    } catch {
      setLoading(false);
      return [];
    }
  }, []);

  const fetchUsageSummary = useCallback(async (): Promise<UsageSummary> => {
    setLoading(true);
    try {
      const res = await api.get<UsageSummary>('/api/v1/billing/usage/summary');
      const summary = mapUsageSummary(res);
      store.setUsageSummary(summary);
      setLoading(false);
      return summary;
    } catch {
      setLoading(false);
      return null as unknown as UsageSummary;
    }
  }, []);

  const fetchOverrides = useCallback(async (): Promise<AdminQuotaOverride[]> => {
    setLoading(true);
    try {
      const res = await api.get<{ overrides: AdminQuotaOverride[] }>('/api/v1/admin/platform/quota-overrides');
      store.setOverrides(res.overrides);
      setLoading(false);
      return res.overrides;
    } catch {
      store.setOverrides([]);
      setLoading(false);
      return [];
    }
  }, []);

  const trackUsage = useCallback(async (
    featureKey: FeatureKey, 
    quantity: number, 
    _metadata?: Record<string, unknown>
  ) => {
    try {
      await api.post('/api/v1/billing/usage/track', { feature_key: featureKey, quantity, metadata: _metadata });
      store.incrementUsage(featureKey, quantity);
    } catch {}
  }, []);

  const getQuotaStatus = useCallback((featureKey: FeatureKey): QuotaStatus | undefined => {
    return store.quotas.find((q) => q.featureKey === featureKey);
  }, []);

  const checkQuota = useCallback((featureKey: FeatureKey, required = 1): QuotaCheckResult => {
    return store.checkQuota(featureKey, required);
  }, []);

  const markAlertRead = useCallback(async (alertId: string) => {
    store.markAlertRead(alertId);
  }, []);

  const dismissAlert = useCallback(async (alertId: string) => {
    store.dismissAlert(alertId);
  }, []);

  const clearAllAlerts = useCallback(async () => {
    store.clearAllAlerts();
  }, []);

  const subscribeToRealtime = useCallback(() => {
    store.toggleRealTime(true);
    
    const interval = setInterval(() => {
      const featureKeys: FeatureKey[] = ['ai_tokens', 'api_requests', 'uploads'];
      const idx = Math.floor(Math.random() * featureKeys.length);
      const randomFeature: FeatureKey = featureKeys[idx]!;
      const randomChange = Math.floor(Math.random() * 5) + 1;
      
      const currentQuota = store.quotas.find((q) => q.featureKey === randomFeature);
      if (currentQuota) {
        const update: RealTimeUsageUpdate = {
          featureKey: randomFeature,
          change: randomChange,
          newTotal: currentQuota.used + randomChange,
          timestamp: new Date().toISOString(),
        };
        store.addRealtimeUpdate(update);
      }
    }, 10000);

    return () => {
      clearInterval(interval);
      store.toggleRealTime(false);
      store.clearRealtimeUpdates();
    };
  }, []);

  const getAllQuotas = useCallback(() => {
    return store.quotas;
  }, []);

  const getActiveAlerts = useCallback(() => {
    return store.alerts.filter((a) => !a.isDismissed);
  }, []);

  const getUsageByCategory = useCallback((): Record<string, QuotaStatus[]> => {
    const categories: Record<string, QuotaStatus[]> = {
      'Documents & Storage': [] as QuotaStatus[],
      'AI & Analysis': [] as QuotaStatus[],
      'Business': [] as QuotaStatus[],
      'Team': [] as QuotaStatus[],
    };

    store.quotas.forEach((quota) => {
      const key = quota.featureKey;
      if (key === 'uploads' || key === 'storage' || key === 'documents' || key === 'exports') {
        categories['Documents & Storage']!.push(quota);
      } else if (key === 'ai_tokens' || key === 'ai_analysis' || key === 'ocr_pages' || key === 'proposal_generations') {
        categories['AI & Analysis']!.push(quota);
      } else if (key === 'tenders' || key === 'bids') {
        categories['Business']!.push(quota);
      } else if (key === 'users' || key === 'api_requests') {
        categories['Team']!.push(quota);
      }
    });

    return categories;
  }, []);

  return {
    quotas: store.quotas,
    alerts: store.alerts,
    usageSummary: store.usageSummary,
    overrides: store.overrides,
    isLoading,
    realtimeUpdates: store.realtimeUpdates,
    fetchQuotas,
    fetchAlerts,
    fetchUsageSummary,
    fetchOverrides,
    trackUsage,
    getQuotaStatus,
    checkQuota,
    markAlertRead,
    dismissAlert,
    clearAllAlerts,
    subscribeToRealtime,
    getAllQuotas,
    getActiveAlerts,
    getUsageByCategory,
  };
}

interface UseQuotaEnforcementReturn {
  canUse: (featureKey: FeatureKey, amount?: number) => boolean;
  checkAndThrow: (featureKey: FeatureKey, amount?: number) => void;
  getEnforcementResult: (featureKey: FeatureKey, amount?: number) => QuotaCheckResult;
}

export function useQuotaEnforcement(): UseQuotaEnforcementReturn {
  const { checkQuota } = useUsageApi();

  const canUse = useCallback((featureKey: FeatureKey, amount = 1): boolean => {
    const result = checkQuota(featureKey, amount);
    return result.allowed;
  }, [checkQuota]);

  const checkAndThrow = useCallback((featureKey: FeatureKey, amount = 1): void => {
    const result = checkQuota(featureKey, amount);
    if (!result.allowed) {
      throw new Error(`Quota exceeded for ${featureKey}. Used: ${result.currentUsage}, Limit: ${result.limit}`);
    }
  }, [checkQuota]);

  const getEnforcementResult = useCallback((featureKey: FeatureKey, amount = 1): QuotaCheckResult => {
    return checkQuota(featureKey, amount);
  }, [checkQuota]);

  return { canUse, checkAndThrow, getEnforcementResult };
}

interface UseAdminOverrideReturn {
  overrides: AdminQuotaOverride[];
  createOverride: (request: OverrideRequest) => Promise<AdminQuotaOverride>;
  revokeOverride: (overrideId: string) => Promise<void>;
  getOverridesForUser: (userId: string) => AdminQuotaOverride[];
  getActiveOverride: (featureKey: FeatureKey, userId?: string) => AdminQuotaOverride | undefined;
}

export function useAdminOverride(): UseAdminOverrideReturn {
  const [overrides, setOverrides] = useState<AdminQuotaOverride[]>([]);

  const createOverride = useCallback(async (request: OverrideRequest): Promise<AdminQuotaOverride> => {
    await new Promise((resolve) => setTimeout(resolve, 500));
    
    const newOverride: AdminQuotaOverride = {
      id: `override-${Date.now()}`,
      userId: request.userId,
      featureKey: request.featureKey,
      newLimit: request.newLimit,
      reason: request.reason,
      grantedBy: 'admin-user',
      grantedByName: 'Admin',
      expiresAt: request.duration 
        ? new Date(Date.now() + parseDuration(request.duration)).toISOString()
        : undefined,
      isActive: true,
      createdAt: new Date().toISOString(),
    };

    setOverrides((prev) => [...prev, newOverride]);
    return newOverride;
  }, []);

  const revokeOverride = useCallback(async (overrideId: string): Promise<void> => {
    await new Promise((resolve) => setTimeout(resolve, 300));
    setOverrides((prev) =>
      prev.map((o) =>
        o.id === overrideId
          ? { ...o, isActive: false, revokedAt: new Date().toISOString() }
          : o
      )
    );
  }, []);

  const getOverridesForUser = useCallback((userId: string): AdminQuotaOverride[] => {
    return overrides.filter((o) => o.userId === userId);
  }, [overrides]);

  const getActiveOverride = useCallback((featureKey: FeatureKey, userId?: string): AdminQuotaOverride | undefined => {
    return overrides.find(
      (o) =>
        o.featureKey === featureKey &&
        o.isActive &&
        (!userId || o.userId === userId) &&
        (!o.expiresAt || new Date(o.expiresAt) > new Date())
    );
  }, [overrides]);

  return {
    overrides,
    createOverride,
    revokeOverride,
    getOverridesForUser,
    getActiveOverride,
  };
}

function parseDuration(duration: string): number {
  const match = duration.match(/^(\d+)([dhms])$/);
  if (!match) return 0;
  
  const value = parseInt(match[1]!, 10);
  const unit = match[2]!;
  
  const multipliers: Record<string, number> = {
    s: 1000,
    m: 60000,
    h: 3600000,
    d: 86400000,
  };
  
  return value * (multipliers[unit] || 0);
}