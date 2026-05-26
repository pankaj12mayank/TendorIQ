'use client';

import { useCallback, useEffect, useState } from 'react';

import { authenticatedFetch } from '@/lib/api-fetch';
import { unwrapData } from '@/lib/api-envelope';

export interface AiProviderOption {
  id: string;
  label: string;
  configured: boolean;
  models: string[];
  default_model?: string;
  hint?: string;
}

export interface AiCatalog {
  default_provider: string;
  default_model: string;
  any_configured: boolean;
  providers: AiProviderOption[];
}

const STORAGE_KEY = 'tendoriq.ai.selection';

export interface AiSelection {
  provider: string;
  model: string;
}

export function loadAiSelection(catalog?: AiCatalog | null): AiSelection {
  if (typeof window !== 'undefined') {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as AiSelection;
        if (parsed.provider && parsed.model) return parsed;
      }
    } catch {
      /* ignore */
    }
  }
  return {
    provider: catalog?.default_provider ?? 'openai',
    model: catalog?.default_model ?? 'gpt-4o-mini',
  };
}

export function saveAiSelection(selection: AiSelection) {
  if (typeof window === 'undefined') return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(selection));
}

export function useAiCatalog() {
  const [catalog, setCatalog] = useState<AiCatalog | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selection, setSelection] = useState<AiSelection>(loadAiSelection());

  const fetchCatalog = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await authenticatedFetch('/api/v1/ai/catalog');
      if (!res.ok) throw new Error('Failed to load AI providers');
      const body = unwrapData(await res.json()) as AiCatalog;
      setCatalog(body);
      const saved = loadAiSelection(body);
      const providerOk = body.providers.some((p) => p.id === saved.provider && p.configured);
      const prov = providerOk
        ? saved.provider
        : body.default_provider;
      const provEntry = body.providers.find((p) => p.id === prov);
      const model =
        saved.model && provEntry?.models.includes(saved.model)
          ? saved.model
          : provEntry?.default_model ?? body.default_model;
      const next = { provider: prov, model };
      setSelection(next);
      saveAiSelection(next);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'AI catalog unavailable');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchCatalog();
  }, [fetchCatalog]);

  const updateSelection = useCallback((next: Partial<AiSelection>) => {
    setSelection((prev) => {
      const merged = { ...prev, ...next };
      saveAiSelection(merged);
      return merged;
    });
  }, []);

  const testConnection = useCallback(async () => {
    const res = await authenticatedFetch('/api/v1/ai/test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        provider: selection.provider,
        model: selection.model,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(
        (err as { error?: { message?: string } })?.error?.message ?? 'Connection test failed'
      );
    }
    return unwrapData(await res.json());
  }, [selection]);

  return {
    catalog,
    loading,
    error,
    selection,
    updateSelection,
    refetch: fetchCatalog,
    testConnection,
  };
}
