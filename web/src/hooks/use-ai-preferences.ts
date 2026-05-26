'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { api } from '@/lib/api-client';
import { unwrapData } from '@/lib/api-envelope';
import { useCurrentUser } from '@/hooks/use-auth';
import { loadAiSelection, saveAiSelection, type AiSelection } from '@/hooks/use-ai-catalog';

export interface AiPreferences extends AiSelection {
  style?: string;
  tone?: string;
}

export function useAiPreferences() {
  const user = useCurrentUser();
  return useQuery({
    queryKey: ['ai-preferences', user?.id],
    queryFn: async () => {
      const raw = await api.get<{ data?: AiPreferences } | AiPreferences>(
        '/api/v1/auth/me/ai-preferences'
      );
      const prefs = unwrapData(raw as { data?: AiPreferences }) as AiPreferences;
      if (prefs.provider && prefs.model) {
        saveAiSelection({ provider: prefs.provider, model: prefs.model });
      }
      return prefs;
    },
    enabled: Boolean(user?.id),
  });
}

export function useUpdateAiPreferences() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: Partial<AiPreferences>) => {
      const raw = await api.patch<{ data?: AiPreferences } | AiPreferences>(
        '/api/v1/auth/me/ai-preferences',
        body
      );
      const prefs = unwrapData(raw as { data?: AiPreferences }) as AiPreferences;
      if (prefs.provider && prefs.model) {
        saveAiSelection({ provider: prefs.provider, model: prefs.model });
      }
      return prefs;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-preferences'] });
    },
  });
}

export function mergePrefsWithLocal(prefs?: AiPreferences | null): AiPreferences {
  const local = loadAiSelection();
  return {
    provider: prefs?.provider ?? local.provider,
    model: prefs?.model ?? local.model,
    style: prefs?.style ?? 'professional',
    tone: prefs?.tone ?? 'formal',
  };
}
