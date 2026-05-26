'use client';

import { useCallback, useState } from 'react';
import { authenticatedJson } from '@/lib/api-fetch';

export type PlatformSettings = {
  pricing?: Record<string, unknown>;
  ai_defaults?: Record<string, unknown>;
  landing?: Record<string, unknown>;
  demo_limits?: Record<string, unknown>;
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

  const loadUploads = useCallback(async () => {
    const res = await authenticatedJson<{ data: AdminUpload[] }>(
      '/api/v1/admin/platform/uploads?limit=100'
    );
    return res.data ?? [];
  }, []);

  return { settings, saving, loadSettings, saveSection, loadUploads };
}
