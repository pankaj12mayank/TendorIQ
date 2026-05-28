'use client';

import { useCallback, useState } from 'react';
import { authenticatedFetch, authenticatedJson } from '@/lib/api-fetch';

export type PlatformSettings = {
  pricing?: Record<string, unknown>;
  ai_defaults?: Record<string, unknown>;
  landing?: Record<string, unknown>;
  demo_limits?: Record<string, unknown>;
  smtp?: Record<string, unknown>;
  payment_gateways?: Record<string, unknown>;
};

export type AdminUpload = {
  id: string;
  name: string;
  file_name: string;
  status: string;
  owner_email: string;
  tenant_name: string;
  created_at: string;
};

export type PlatformUserRow = {
  id: string;
  name: string;
  email: string;
  role: string;
  membership_role?: string;
  status: 'active' | 'inactive' | 'deleted' | string;
  organization: string;
  plan?: string;
};

export type LandingCmsState = {
  version: number;
  status: string;
  draft: Record<string, unknown>;
  published: Record<string, unknown>;
  history: Array<{ id: string; created_at: string; version: number }>;
  published_at?: string | null;
  updated_at?: string | null;
};

export function useAdminPlatform() {
  const [settings, setSettings] = useState<PlatformSettings | null>(null);
  const [saving, setSaving] = useState(false);

  const loadSettings = useCallback(async () => {
    const res = await authenticatedJson<{ data: PlatformSettings }>(
      '/api/v1/admin/platform/settings'
    );
    setSettings(res.data ?? null);
    return res.data;
  }, []);

  const saveSection = useCallback(
    async (section: keyof PlatformSettings, data: Record<string, unknown>) => {
      setSaving(true);
      try {
        const res = await authenticatedJson<{ data: Record<string, unknown> }>(
          '/api/v1/admin/platform/settings',
          {
            method: 'PATCH',
            body: JSON.stringify({ section, data }),
          }
        );
        const merged = res.data?.[section] as Record<string, unknown> | undefined;
        if (merged) {
          setSettings((prev) => ({ ...prev, [section]: merged }));
        } else {
          await loadSettings();
        }
      } finally {
        setSaving(false);
      }
    },
    [loadSettings]
  );

  const loadUploads = useCallback(async (params?: Record<string, string | number | undefined>) => {
    const qs = new URLSearchParams();
    Object.entries(params ?? {}).forEach(([k, v]) => {
      if (v !== undefined && v !== null && String(v) !== '') qs.set(k, String(v));
    });
    const res = await authenticatedJson<{ data: AdminUpload[] }>(
      `/api/v1/admin/platform/uploads?${qs.toString() || 'limit=100'}`
    );
    return res.data ?? [];
  }, []);

  const loadUsers = useCallback(
    async (params?: Record<string, string | number | undefined>) => {
      const qs = new URLSearchParams();
      Object.entries(params ?? {}).forEach(([k, v]) => {
        if (v !== undefined && v !== null && String(v) !== '') qs.set(k, String(v));
      });
      const res = await authenticatedJson<{
        data: PlatformUserRow[];
        pagination?: Record<string, unknown>;
      }>(`/api/v1/admin/platform/users?${qs.toString()}`);
      return { rows: res.data ?? [], pagination: res.pagination ?? {} };
    },
    []
  );

  const loadUserDetail = useCallback(async (userId: string) => {
    const res = await authenticatedJson<{ data: Record<string, unknown> }>(
      `/api/v1/admin/platform/users/${userId}`
    );
    return res.data ?? {};
  }, []);

  const updateUserStatus = useCallback(async (userId: string, status: 'active' | 'inactive') => {
    await authenticatedJson(`/api/v1/admin/platform/users/${userId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    });
  }, []);

  const deleteUser = useCallback(async (userId: string) => {
    await authenticatedJson(`/api/v1/admin/platform/users/${userId}`, { method: 'DELETE' });
  }, []);

  const restoreUser = useCallback(async (userId: string) => {
    await authenticatedJson(`/api/v1/admin/platform/users/${userId}/restore`, { method: 'POST' });
  }, []);

  const loadOwnerProfile = useCallback(async () => {
    const res = await authenticatedJson<{ data: Record<string, unknown> }>(
      '/api/v1/admin/platform/owner/profile'
    );
    return res.data ?? {};
  }, []);

  const saveOwnerProfile = useCallback(async (body: Record<string, unknown>) => {
    const res = await authenticatedJson<{ data: Record<string, unknown> }>(
      '/api/v1/admin/platform/owner/profile',
      {
        method: 'PATCH',
        body: JSON.stringify(body),
      }
    );
    return res.data ?? {};
  }, []);

  const uploadOwnerAsset = useCallback(async (kind: 'avatar' | 'logo' | 'favicon', file: File) => {
    const fd = new FormData();
    fd.append('kind', kind);
    fd.append('file', file);
    const res = await authenticatedFetch('/api/v1/admin/platform/owner/profile/upload', {
      method: 'POST',
      body: fd,
    });
    if (!res.ok) throw new Error('Asset upload failed');
    const json = (await res.json()) as { data?: Record<string, unknown> };
    return json.data ?? {};
  }, []);

  const uploadCmsAsset = useCallback(async (file: File) => {
    const fd = new FormData();
    fd.append('file', file);
    const res = await authenticatedFetch('/api/v1/admin/platform/cms/assets/upload', {
      method: 'POST',
      body: fd,
    });
    if (!res.ok) throw new Error('CMS image upload failed');
    const json = (await res.json()) as { data?: Record<string, unknown> };
    return json.data ?? {};
  }, []);

  const loadPaymentSettings = useCallback(async () => {
    const res = await authenticatedJson<{ data: Record<string, unknown> }>(
      '/api/v1/admin/platform/settings/payments'
    );
    return res.data ?? {};
  }, []);

  const savePaymentSettings = useCallback(async (data: Record<string, unknown>) => {
    const res = await authenticatedJson<{ data: Record<string, unknown> }>(
      '/api/v1/admin/platform/settings/payments',
      {
        method: 'PATCH',
        body: JSON.stringify(data),
      }
    );
    return res.data ?? {};
  }, []);

  const testPaymentSettings = useCallback(async (gateway: 'razorpay' | 'stripe') => {
    await authenticatedJson('/api/v1/admin/platform/settings/payments/test', {
      method: 'POST',
      body: JSON.stringify({ gateway }),
    });
  }, []);

  const loadPaymentHistory = useCallback(async (params?: Record<string, string | number | undefined>) => {
    const qs = new URLSearchParams();
    Object.entries(params ?? {}).forEach(([k, v]) => {
      if (v !== undefined && v !== null && String(v) !== '') qs.set(k, String(v));
    });
    return await authenticatedJson(`/api/v1/admin/platform/payments/history?${qs.toString()}`);
  }, []);

  const saveBillingPricing = useCallback(async (data: Record<string, unknown>) => {
    return await authenticatedJson('/api/v1/admin/platform/billing/pricing', {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }, []);

  const searchAnalyticsUser = useCallback(async (q: string, page = 1, limit = 20) => {
    const term = q.trim();
    if (!term) {
      return { data: [], pagination: { page, limit, total: 0 } };
    }
    return await authenticatedJson(
      `/api/v1/admin/platform/analytics/user-search?q=${encodeURIComponent(term)}&page=${page}&limit=${limit}`
    );
  }, []);

  const deleteUpload = useCallback(async (documentId: string) => {
    await authenticatedJson(`/api/v1/admin/platform/uploads/${documentId}`, { method: 'DELETE' });
  }, []);

  const batchDeleteUploads = useCallback(async (documentIds: string[]) => {
    await authenticatedJson('/api/v1/admin/platform/uploads/batch-delete', {
      method: 'POST',
      body: JSON.stringify({ document_ids: documentIds }),
    });
  }, []);

  const loadSmtpSettings = useCallback(async () => {
    const res = await authenticatedJson<{ data: Record<string, unknown> }>(
      '/api/v1/admin/platform/settings/smtp'
    );
    return res.data ?? {};
  }, []);

  const saveSmtpSettings = useCallback(async (data: Record<string, unknown>) => {
    setSaving(true);
    try {
      const res = await authenticatedJson<{ data: Record<string, unknown> }>(
        '/api/v1/admin/platform/settings/smtp',
        {
          method: 'PATCH',
          body: JSON.stringify(data),
        }
      );
      setSettings((prev) => ({ ...(prev ?? {}), smtp: res.data ?? {} }));
      return res.data ?? {};
    } finally {
      setSaving(false);
    }
  }, []);

  const testSmtpSettings = useCallback(async (toEmail: string) => {
    await authenticatedJson('/api/v1/admin/platform/settings/smtp/test', {
      method: 'POST',
      body: JSON.stringify({ to_email: toEmail }),
    });
  }, []);

  const loadCms = useCallback(async () => {
    const res = await authenticatedJson<{ data: LandingCmsState }>('/api/v1/admin/platform/cms');
    return res.data;
  }, []);

  const saveCmsDraft = useCallback(
    async (modules: Record<string, unknown>, expectedVersion?: number) => {
      const res = await authenticatedJson<{ data: LandingCmsState }>('/api/v1/admin/platform/cms/draft', {
        method: 'PATCH',
        body: JSON.stringify({ modules, expected_version: expectedVersion }),
      });
      return res.data;
    },
    []
  );

  const publishCms = useCallback(async () => {
    const res = await authenticatedJson<{ data: LandingCmsState }>('/api/v1/admin/platform/cms/publish', {
      method: 'POST',
    });
    return res.data;
  }, []);

  const rollbackCms = useCallback(async (revisionId: string) => {
    const res = await authenticatedJson<{ data: LandingCmsState }>(
      `/api/v1/admin/platform/cms/rollback/${revisionId}`,
      { method: 'POST' }
    );
    return res.data;
  }, []);

  return {
    settings,
    saving,
    loadSettings,
    saveSection,
    loadUploads,
    loadUsers,
    loadUserDetail,
    updateUserStatus,
    deleteUser,
    restoreUser,
    loadOwnerProfile,
    saveOwnerProfile,
    uploadOwnerAsset,
    uploadCmsAsset,
    loadSmtpSettings,
    saveSmtpSettings,
    testSmtpSettings,
    loadCms,
    saveCmsDraft,
    publishCms,
    rollbackCms,
    loadPaymentSettings,
    savePaymentSettings,
    testPaymentSettings,
    loadPaymentHistory,
    saveBillingPricing,
    searchAnalyticsUser,
    deleteUpload,
    batchDeleteUploads,
  };
}
