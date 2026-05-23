import { useCallback, useState } from 'react';
import { toast } from 'sonner';

import {
  PLATFORM_AUDIT_EXPORT_MAX_ROWS,
  PLATFORM_AUDIT_LIST_LIMIT,
} from '@/lib/audit-constants';
import { api, ApiError } from '@/lib/api-client';
import {
  PLATFORM_AUDIT_EXPORT_MAX_ROWS,
  PLATFORM_AUDIT_LIST_LIMIT,
} from '@/lib/audit-constants';
import {
  parsePlatformAuditLogsResponse,
  parsePlatformFailedJobsResponse,
  parsePlatformProvidersResponse,
  parsePlatformQueueJobsResponse,
  parsePlatformUsersResponse,
} from '@/lib/admin-platform-api';
import { useAdminStore } from '@/components/admin/store';
import {
  User,
  UserRole,
  BillingPlan,
  AIProvider,
  PromptTemplate,
  QueueJob,
  AuditLogEntry,
  FailedJob,
  AdvancedFilter,
} from '@/components/admin/types';

function handleApiError(err: unknown, fallback: string) {
  const msg = err instanceof ApiError ? err.message : err instanceof Error ? err.message : fallback;
  toast.error(msg);
  throw err;
}

// --- Users ---

export function useAdminUsersApi() {
  const { users, setUsers, isLoading, setLoading } = useAdminStore();
  const [isError, setIsError] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchUsers = useCallback(
    async (filters?: AdvancedFilter[]) => {
      setIsError(false);
      setError(null);
      setLoading(true);
      try {
        const params: Record<string, string | number | boolean> = {};
        if (filters?.length) {
          filters.forEach((f, i) => {
            params[`filter_${i}_field`] = f.field;
            params[`filter_${i}_op`] = f.operator;
            params[`filter_${i}_value`] = Array.isArray(f.value) ? f.value.join(',') : f.value;
          });
        }
        const res = await api.get<unknown>('/api/v1/admin/platform/users', { params });
        setUsers(parsePlatformUsersResponse(res).users);
      } catch (err) {
        setIsError(true);
        setError('Failed to fetch users');
        handleApiError(err, 'Failed to fetch users');
      } finally {
        setLoading(false);
      }
    },
    [setUsers, setLoading]
  );

  const createUser = useCallback(
    async (userData: Partial<User>) => {
      setLoading(true);
      try {
        const created = await api.post<User>('/api/v1/admin/platform/users', {
          name: userData.name,
          email: userData.email,
          role: userData.role || 'viewer',
          status: userData.status || 'active',
          organization: userData.organization,
        });
        useAdminStore.getState().addUser(created);
        toast.success('User created successfully');
      } catch (err) {
        handleApiError(err, 'Unable to create user');
      } finally {
        setLoading(false);
      }
    },
    [setLoading]
  );

  const updateUser = useCallback(
    async (id: string, data: Partial<User>) => {
      setLoading(true);
      try {
        const updated = await api.patch<User>(`/api/v1/admin/platform/users/${id}`, data);
        useAdminStore.getState().updateUser(id, updated);
        toast.success('User updated');
      } catch (err) {
        handleApiError(err, 'Unable to save changes');
      } finally {
        setLoading(false);
      }
    },
    [setLoading]
  );

  const deleteUser = useCallback(
    async (id: string) => {
      setLoading(true);
      try {
        await api.delete(`/api/v1/admin/platform/users/${id}`);
        useAdminStore.getState().deleteUser(id);
        toast.success('User removed');
      } catch (err) {
        handleApiError(err, 'Unable to delete user');
      } finally {
        setLoading(false);
      }
    },
    [setLoading]
  );

  const updateUserRole = useCallback(
    async (id: string, role: UserRole) => {
      await updateUser(id, { role });
    },
    [updateUser]
  );

  const toggleUserStatus = useCallback(
    async (id: string) => {
      const user = useAdminStore.getState().users.find((u) => u.id === id);
      if (!user) return;
      const newStatus = user.status === 'active' ? 'inactive' : 'active';
      await updateUser(id, { status: newStatus });
    },
    [updateUser]
  );

  return {
    users,
    isLoading,
    isError,
    error,
    fetchUsers,
    createUser,
    updateUser,
    deleteUser,
    updateUserRole,
    toggleUserStatus,
  };
}

// --- Billing ---

export function useBillingApi() {
  const [plans, setPlans] = useState<BillingPlan[]>([]);
  const [subscriptions, setSubscriptions] = useState<unknown[]>([]);
  const [isLoading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchBilling = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get<{
        plans: BillingPlan[];
        subscriptions: unknown[];
        invoices: unknown[];
      }>('/api/v1/admin/platform/billing');
      setPlans(res.plans);
      setSubscriptions(res.subscriptions);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to load billing');
      handleApiError(err, 'Billing data could not be loaded');
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    plans,
    subscriptions,
    isLoading,
    error,
    fetchBilling,
    createPlan: async () => {
      toast.info('Plan changes are managed in billing configuration');
    },
    updatePlan: async () => {
      toast.info('Plan changes are managed in billing configuration');
    },
    deletePlan: async () => {
      toast.info('Plan changes are managed in billing configuration');
    },
  };
}

// --- AI providers ---

export function useAIProvidersApi() {
  const [providers, setProviders] = useState<AIProvider[]>([]);
  const [isLoading, setLoading] = useState(false);

  const fetchProviders = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get<unknown>('/api/v1/admin/platform/ai-providers');
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
      handleApiError(err, 'Failed to load AI providers');
    } finally {
      setLoading(false);
    }
  }, []);

  const addProvider = useCallback(
    async (data: Partial<AIProvider> & { api_key?: string }) => {
      setLoading(true);
      try {
        await api.post('/api/v1/admin/platform/ai-providers', {
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
        handleApiError(err, 'Unable to add provider');
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
        await api.patch(`/api/v1/admin/platform/ai-providers/${id}`, data);
        toast.success('Provider updated');
        await fetchProviders();
      } catch (err) {
        handleApiError(err, 'Unable to update provider');
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
        await api.delete(`/api/v1/admin/platform/ai-providers/${id}`);
        toast.success('Provider deleted');
        await fetchProviders();
      } catch (err) {
        handleApiError(err, 'Unable to delete provider');
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
      const res = await api.post<{ success: boolean; message: string }>(
        `/api/v1/admin/platform/ai-providers/${id}/test`
      );
      if (res.success) toast.success(res.message);
      else toast.error(res.message);
    } catch (err) {
      handleApiError(err, 'Provider test failed');
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

// --- Prompts ---

function mapPrompt(row: Record<string, unknown>): PromptTemplate {
  return {
    id: String(row.id ?? row.name),
    name: String(row.name ?? ''),
    description: String(row.description ?? ''),
    category: String(row.category ?? 'custom'),
    content: String(row.content ?? ''),
    variables: Array.isArray(row.variables)
      ? row.variables.map((v: { name?: string }) => ({
          name: v.name ?? 'var',
          type: 'string' as const,
          required: true,
        }))
      : [],
    version: Number(row.version ?? 1),
    isActive: Boolean(row.is_active ?? row.isActive ?? true),
    createdAt: String(row.created_at ?? new Date().toISOString()),
    updatedAt: String(row.updated_at ?? new Date().toISOString()),
    createdBy: String(row.created_by ?? 'System'),
  };
}

export function usePromptsApi() {
  const [prompts, setPrompts] = useState<PromptTemplate[]>([]);
  const [isLoading, setLoading] = useState(false);

  const fetchPrompts = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get<{ items?: unknown[]; prompts?: unknown[] } | unknown[]>(
        '/api/v1/prompts'
      );
      const list = Array.isArray(res)
        ? res
        : (res as { items?: unknown[] }).items ?? (res as { prompts?: unknown[] }).prompts ?? [];
      setPrompts(list.map((r) => mapPrompt(r as Record<string, unknown>)));
    } catch (err) {
      handleApiError(err, 'Failed to load prompts');
    } finally {
      setLoading(false);
    }
  }, []);

  const createPrompt = useCallback(
    async (data: Partial<PromptTemplate>) => {
      setLoading(true);
      try {
        await api.post('/api/v1/prompts', {
          name: data.name,
          description: data.description,
          prompt_type: data.category || 'custom',
          category: data.category,
          content: data.content,
          variables: (data.variables || []).map((v) => v.name),
          is_active: data.isActive ?? true,
        });
        toast.success('Prompt created');
        await fetchPrompts();
      } catch (err) {
        handleApiError(err, 'Unable to create prompt');
      } finally {
        setLoading(false);
      }
    },
    [fetchPrompts]
  );

  const updatePrompt = useCallback(
    async (id: string, data: Partial<PromptTemplate>) => {
      setLoading(true);
      try {
        await api.put(`/api/v1/prompts/${id}`, data);
        toast.success('Prompt updated');
        await fetchPrompts();
      } catch (err) {
        handleApiError(err, 'Unable to update prompt');
      } finally {
        setLoading(false);
      }
    },
    [fetchPrompts]
  );

  const deletePrompt = useCallback(
    async (id: string) => {
      setLoading(true);
      try {
        await api.delete(`/api/v1/prompts/${id}`);
        toast.success('Prompt deleted');
        await fetchPrompts();
      } catch (err) {
        handleApiError(err, 'Unable to delete prompt');
      } finally {
        setLoading(false);
      }
    },
    [fetchPrompts]
  );

  const togglePromptActive = useCallback(
    async (id: string) => {
      const p = prompts.find((x) => x.id === id);
      if (!p) return;
      await updatePrompt(id, { isActive: !p.isActive });
    },
    [prompts, updatePrompt]
  );

  const testPrompt = useCallback(async (id: string, variables: Record<string, unknown>) => {
    setLoading(true);
    try {
      const p = prompts.find((x) => x.id === id);
      let result = p?.content || '';
      Object.entries(variables).forEach(([k, v]) => {
        result = result.replace(`{${k}}`, String(v));
      });
      toast.success('Prompt preview ready');
      return result;
    } finally {
      setLoading(false);
    }
  }, [prompts]);

  return {
    prompts,
    isLoading,
    fetchPrompts,
    createPrompt,
    updatePrompt,
    deletePrompt,
    togglePromptActive,
    testPrompt,
  };
}

// --- Queue ---

export function useQueueApi() {
  const [jobs, setJobs] = useState<QueueJob[]>([]);
  const [isLoading, setLoading] = useState(false);

  const refreshJobs = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get<unknown>('/api/v1/admin/platform/queue/jobs');
      setJobs(parsePlatformQueueJobsResponse(res));
    } catch (err) {
      handleApiError(err, 'Failed to load queue');
    } finally {
      setLoading(false);
    }
  }, []);

  const retryJob = useCallback(
    async (id: string) => {
      try {
        await api.post(`/api/v1/admin/platform/queue/jobs/${id}/retry`);
        toast.success('Job retry scheduled');
        await refreshJobs();
      } catch (err) {
        handleApiError(err, 'Retry failed');
      }
    },
    [refreshJobs]
  );

  const cancelJob = useCallback(
    async (id: string) => {
      try {
        await api.post(`/api/v1/admin/platform/queue/jobs/${id}/cancel`);
        toast.success('Job cancelled');
        await refreshJobs();
      } catch (err) {
        handleApiError(err, 'Failed to cancel job');
      }
    },
    [refreshJobs]
  );

  const pauseJob = useCallback(async (id: string) => {
    try {
      await api.post(`/api/v1/admin/platform/queue/jobs/${id}/pause`);
      toast.success('Job paused');
      await refreshJobs();
    } catch (err) {
      handleApiError(err, 'Failed to pause job');
    }
  }, [refreshJobs]);

  const resumeJob = useCallback(async (id: string) => {
    try {
      await api.post(`/api/v1/admin/platform/queue/jobs/${id}/resume`);
      toast.success('Job resumed');
      await refreshJobs();
    } catch (err) {
      handleApiError(err, 'Failed to resume job');
    }
  }, [refreshJobs]);

  return { jobs, isLoading, refreshJobs, retryJob, cancelJob, pauseJob, resumeJob };
}

// --- Audit ---

export function useAuditLogApi() {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [isLoading, setLoading] = useState(false);

  const fetchLogs = useCallback(async (_filters?: AdvancedFilter[]) => {
    setLoading(true);
    try {
      const res = await api.get<unknown>('/api/v1/admin/platform/audit-logs', {
        params: { limit: PLATFORM_AUDIT_LIST_LIMIT },
      });
      setLogs(parsePlatformAuditLogsResponse(res));
    } catch (err) {
      handleApiError(err, 'Failed to load audit logs');
    } finally {
      setLoading(false);
    }
  }, []);

  const exportLogs = useCallback(async (format: 'csv' | 'json') => {
    setLoading(true);
    try {
      const res = await api.post<{ content: string | unknown; mime_type: string }>(
        '/api/v1/admin/platform/audit-logs/export',
        { format, limit: PLATFORM_AUDIT_EXPORT_MAX_ROWS }
      );
      const body =
        typeof res.content === 'string' ? res.content : JSON.stringify(res.content, null, 2);
      const mime = res.mime_type || (format === 'csv' ? 'text/csv' : 'application/json');
      const blob = new Blob([body], { type: mime });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `audit-logs.${format}`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success('Audit log export downloaded');
    } catch (err) {
      handleApiError(err, 'Export failed');
    } finally {
      setLoading(false);
    }
  }, []);

  const getLogById = useCallback(
    (id: string) => logs.find((l) => l.id === id),
    [logs]
  );

  return { logs, isLoading, fetchLogs, exportLogs, getLogById };
}

// --- Failed jobs ---

export function useFailedJobsApi() {
  const [jobs, setJobs] = useState<FailedJob[]>([]);
  const [isLoading, setLoading] = useState(false);

  const fetchFailedJobs = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get<unknown>('/api/v1/admin/platform/failed-jobs');
      setJobs(parsePlatformFailedJobsResponse(res));
    } catch (err) {
      handleApiError(err, 'Failed to load failed jobs');
    } finally {
      setLoading(false);
    }
  }, []);

  const retryJob = useCallback(
    async (id: string) => {
      try {
        await api.post(`/api/v1/admin/platform/queue/jobs/${id}/retry`);
        await api.delete(`/api/v1/admin/platform/failed-jobs/${id}`);
        setJobs((prev) => prev.filter((j) => j.id !== id));
        toast.success('Job retry scheduled');
      } catch (err) {
        handleApiError(err, 'Retry failed');
      }
    },
    []
  );

  const retryAll = useCallback(async () => {
    const retryable = jobs.filter((j) => j.retryable);
    await Promise.allSettled(retryable.map((j) => retryJob(j.id)));
  }, [jobs, retryJob]);

  const deleteJob = useCallback(
    async (id: string) => {
      try {
        await api.delete(`/api/v1/admin/platform/failed-jobs/${id}`);
        setJobs((prev) => prev.filter((j) => j.id !== id));
        toast.success('Failed job dismissed');
      } catch (err) {
        handleApiError(err, 'Unable to remove job');
      }
    },
    []
  );

  const clearAll = useCallback(async () => {
    await Promise.allSettled(jobs.map((j) => api.delete(`/api/v1/admin/platform/failed-jobs/${j.id}`)));
    setJobs([]);
    toast.success('Failed jobs cleared');
  }, [jobs]);

  return {
    jobs,
    isLoading,
    fetchFailedJobs,
    retryJob,
    retryAll,
    deleteJob,
    clearAll,
  };
}
