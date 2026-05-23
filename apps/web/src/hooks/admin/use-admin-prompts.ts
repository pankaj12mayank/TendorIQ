import { useCallback, useState } from 'react';
import { toast } from 'sonner';

import { api } from '@/lib/api-client';
import { PROMPTS_PATHS } from '@/lib/admin-platform-paths';
import { PromptTemplate } from '@/components/admin/types';

import { reportAdminApiError } from './admin-api-errors';

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
        PROMPTS_PATHS.list
      );
      const list = Array.isArray(res)
        ? res
        : (res as { items?: unknown[] }).items ?? (res as { prompts?: unknown[] }).prompts ?? [];
      setPrompts(list.map((r) => mapPrompt(r as Record<string, unknown>)));
    } catch (err) {
      reportAdminApiError(err, 'Failed to load prompts');
    } finally {
      setLoading(false);
    }
  }, []);

  const createPrompt = useCallback(
    async (data: Partial<PromptTemplate>) => {
      setLoading(true);
      try {
        await api.post(PROMPTS_PATHS.list, {
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
        reportAdminApiError(err, 'Unable to create prompt');
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
        await api.put(PROMPTS_PATHS.item(id), data);
        toast.success('Prompt updated');
        await fetchPrompts();
      } catch (err) {
        reportAdminApiError(err, 'Unable to update prompt');
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
        await api.delete(PROMPTS_PATHS.item(id));
        toast.success('Prompt deleted');
        await fetchPrompts();
      } catch (err) {
        reportAdminApiError(err, 'Unable to delete prompt');
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

  const testPrompt = useCallback(
    async (id: string, variables: Record<string, unknown>) => {
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
    },
    [prompts]
  );

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
