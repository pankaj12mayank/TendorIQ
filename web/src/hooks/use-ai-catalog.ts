'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

import { authenticatedFetch } from '@/lib/api-fetch';
import { unwrapData } from '@/lib/api-envelope';

export interface AiProviderOption {
  id: string;
  label: string;
  configured: boolean;
  online?: boolean;
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
const CATALOG_POLL_MS = 20_000;

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

/** Resolve provider/model from API catalog (live keys + Ollama tags). */
export function resolveSelectionFromCatalog(
  catalog: AiCatalog,
  saved?: AiSelection | null
): AiSelection {
  const configured = catalog.providers.filter((p) => p.configured && p.models.length > 0);
  if (!configured.length) {
    return {
      provider: catalog.default_provider,
      model: catalog.default_model,
    };
  }

  const trySaved = saved ?? loadAiSelection(catalog);
  const savedProvider = configured.find((p) => p.id === trySaved.provider);
  if (savedProvider) {
    const model = savedProvider.models.includes(trySaved.model)
      ? trySaved.model
      : savedProvider.default_model && savedProvider.models.includes(savedProvider.default_model)
        ? savedProvider.default_model
        : savedProvider.models[0];
    return { provider: savedProvider.id, model };
  }

  const preferred = configured.find((p) => p.id === catalog.default_provider) ?? configured[0];
  const model =
    preferred.default_model && preferred.models.includes(preferred.default_model)
      ? preferred.default_model
      : preferred.models[0];
  return { provider: preferred.id, model };
}

export function useAiCatalog(options?: { poll?: boolean }) {
  const poll = options?.poll !== false;
  const [catalog, setCatalog] = useState<AiCatalog | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selection, setSelection] = useState<AiSelection>(loadAiSelection());
  const selectionRef = useRef(selection);

  useEffect(() => {
    selectionRef.current = selection;
  }, [selection]);

  const applyCatalog = useCallback((body: AiCatalog) => {
    setCatalog(body);
    const saved = loadAiSelection(body);
    const next = resolveSelectionFromCatalog(body, saved);
    const prev = selectionRef.current;
    const changed = prev.provider !== next.provider || prev.model !== next.model;
    setSelection(next);
    saveAiSelection(next);
    return { next, changed };
  }, []);

  const fetchCatalog = useCallback(async (opts?: { silent?: boolean }) => {
    if (!opts?.silent) {
      setLoading(true);
    }
    setError(null);
    try {
      const res = await authenticatedFetch('/api/v1/ai/catalog');
      if (!res.ok) throw new Error('Failed to load AI providers');
      const body = unwrapData(await res.json()) as AiCatalog;
      return applyCatalog(body);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'AI catalog unavailable');
      return null;
    } finally {
      if (!opts?.silent) {
        setLoading(false);
      }
    }
  }, [applyCatalog]);

  useEffect(() => {
    void fetchCatalog();
  }, [fetchCatalog]);

  useEffect(() => {
    if (!poll) return;
    const onFocus = () => void fetchCatalog({ silent: true });
    window.addEventListener('focus', onFocus);
    const timer = window.setInterval(() => void fetchCatalog({ silent: true }), CATALOG_POLL_MS);
    return () => {
      window.removeEventListener('focus', onFocus);
      window.clearInterval(timer);
    };
  }, [fetchCatalog, poll]);

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
        provider: selectionRef.current.provider,
        model: selectionRef.current.model,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(
        (err as { error?: { message?: string } })?.error?.message ?? 'Connection test failed'
      );
    }
    return unwrapData(await res.json());
  }, []);

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
