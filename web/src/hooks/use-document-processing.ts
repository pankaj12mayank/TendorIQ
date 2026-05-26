'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

import { authenticatedFetch } from '@/lib/api-fetch';
import { unwrapData } from '@/lib/api-envelope';

export interface ProcessingStatus {
  document_id: string;
  processing_status: string;
  processing_error?: string | null;
  tender_id?: string | null;
  analysis?: {
    status?: string;
    tender_id?: string;
    analysis_id?: string;
    error?: string;
  };
}

export function useDocumentProcessing(documentId?: string, pollMs = 3000) {
  const [status, setStatus] = useState<ProcessingStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchStatus = useCallback(async () => {
    if (!documentId) return null;
    const res = await authenticatedFetch(`/api/v1/processing/documents/${documentId}`);
    if (!res.ok) throw new Error('Failed to fetch processing status');
    const data = unwrapData(await res.json()) as ProcessingStatus;
    setStatus(data);
    return data;
  }, [documentId]);

  const startAnalysis = useCallback(
    async (opts?: { provider?: string; model?: string; async_mode?: boolean }) => {
      if (!documentId) throw new Error('No document id');
      setLoading(true);
      try {
        const res = await authenticatedFetch(
          `/api/v1/processing/documents/${documentId}/analyze`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              provider: opts?.provider,
              model: opts?.model,
              async_mode: opts?.async_mode ?? true,
            }),
          }
        );
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(
            (err as { error?: { message?: string } })?.error?.message ?? 'Analysis failed to start'
          );
        }
        await fetchStatus();
        return unwrapData(await res.json());
      } finally {
        setLoading(false);
      }
    },
    [documentId, fetchStatus]
  );

  const retryAnalysis = useCallback(
    async (provider?: string, model?: string) => {
      if (!documentId) throw new Error('No document id');
      const params = new URLSearchParams();
      if (provider) params.set('provider', provider);
      if (model) params.set('model', model);
      const q = params.toString() ? `?${params}` : '';
      const res = await authenticatedFetch(
        `/api/v1/processing/documents/${documentId}/retry${q}`,
        { method: 'POST' }
      );
      if (!res.ok) throw new Error('Retry failed');
      await fetchStatus();
      return unwrapData(await res.json());
    },
    [documentId, fetchStatus]
  );

  useEffect(() => {
    if (!documentId) return;
    void fetchStatus();
    timerRef.current = setInterval(() => {
      void fetchStatus();
    }, pollMs);
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [documentId, fetchStatus, pollMs]);

  useEffect(() => {
    if (!status) return;
    const done = ['completed', 'failed'].includes(status.processing_status);
    if (done && timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, [status]);

  const isProcessing = status?.processing_status === 'processing' || status?.processing_status === 'retrying';
  const isComplete = status?.processing_status === 'completed';
  const isFailed = status?.processing_status === 'failed';

  return {
    status,
    loading,
    isProcessing,
    isComplete,
    isFailed,
    tenderId: status?.tender_id ?? status?.analysis?.tender_id,
    fetchStatus,
    startAnalysis,
    retryAnalysis,
  };
}
