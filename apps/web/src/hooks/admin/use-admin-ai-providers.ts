import { useCallback, useState } from 'react';
import { toast } from 'sonner';

import { api } from '@/lib/api-client';
import { ADMIN_PLATFORM_PATHS } from '@/lib/admin-platform-paths';
import { parsePlatformProvidersResponse } from '@/lib/admin-platform-api';
import { AIProvider } from '@/components/admin/types';

import { reportAdminApiError } from './admin-api-errors';

export function useAIProvidersApi() {
  const [providers, setProviders] = useState<AIProvider[]>([]);
  const [isLoading, setLoading] = useState(false);

  const fetchProviders = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get<unknown>(ADMIN_PLATFORM_PATHS.aiProviders);
      setProviders(
        parsePlatformProvidersResponse(res).map((p) => {
          const row = p as AIProvider & { api_key_masked?: string; is_active?: boolean; is_default?: boolean };
          return {
            ...row,
            apiKeyMasked: row.apiKeyMasked ?? row.api_key_masked ?? '',
            isActive: row.isActive ?? row.is_active ?? true,
          };
        })
      );
    } catch (err) {
      reportAdminApiError(err, 'Failed to load AI providers');
    } finally {
      setLoading(false);
    }
  }, []);

  const addProvider = useCallback(
    async (data: Partial<AIProvider> & { api_key?: string }) => {
      setLoading(true);
      try {
        await api.post(ADMIN_PLATFORM_PATHS.aiProviders, {
          name: data.name,
          type: data.type || 'ollama',
          base_url: (data as { base_url?: string }).base_url,
          api_key: data.api_key,
          is_active: data.isActive ?? true,
          models: data.models || [],
          settings: data.settings,
        });
        toast.success('Provider added');
        await fetchProviders();
      } catch (err) {
        reportAdminApiError(err, 'Unable to add provider');
      } finally {
        setLoading(false);
      }
    },
    [fetchProviders]
  );

  const updateProvider = useCallback(
    async (id: string, data: Partial<AIProvider> & { api_key?: string }) => {
      setLoading(true);
      try {
        await api.patch(`${ADMIN_PLATFORM_PATHS.aiProviders}/${id}`, data);
        toast.success('Provider updated');
        await fetchProviders();
      } catch (err) {
        reportAdminApiError(err, 'Unable to update provider');
      } finally {
        setLoading(false);
      }
    },
    [fetchProviders]
  );

  const deleteProvider = useCallback(
    async (id: string) => {
      setLoading(true);
      try {
        await api.delete(`${ADMIN_PLATFORM_PATHS.aiProviders}/${id}`);
        toast.success('Provider deleted');
        await fetchProviders();
      } catch (err) {
        reportAdminApiError(err, 'Unable to delete provider');
      } finally {
        setLoading(false);
      }
    },
    [fetchProviders]
  );

  const toggleProvider = useCallback(
    async (id: string) => {
      const p = providers.find((x) => x.id === id);
      if (!p) return;
      await updateProvider(id, { isActive: !p.isActive });
    },
    [providers, updateProvider]
  );

  const testProvider = useCallback(async (id: string) => {
    setLoading(true);
    try {
      const res = await api.post<{ success: boolean; message: string; dry_run?: boolean }>(
        ADMIN_PLATFORM_PATHS.aiProviderTest(id)
      );
      if (res.success) toast.success(res.message);
      else toast.error(res.message);
    } catch (err) {
      reportAdminApiError(err, 'Provider test failed');
    } finally {
      setLoading(false);
    }
  }, []);

  const updateSettings = useCallback(
    async (providerId: string, settings: AIProvider['settings']) => {
      await updateProvider(providerId, { settings });
    },
    [updateProvider]
  );

  return {
    providers,
    isLoading,
    fetchProviders,
    addProvider,
    updateProvider,
    deleteProvider,
    toggleProvider,
    testProvider,
    updateSettings,
  };
}
