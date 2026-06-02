import { useCallback, useState, useRef, useEffect } from 'react';
import { api } from '@/lib/api-client';
import {
  unwrapDocumentPayload,
  type DocumentListResponse,
} from '@/lib/documents-api';
import { useDocumentStore, Document, DocumentStats, DocumentFilters, DocumentStatus } from '@/stores/document-store';
import { appToast } from '@/lib/app-toast';
import { formatPollingError, PollingCancelledError, PollingTimeoutError } from '@/lib/polling-errors';

export interface DocumentStatsResponse {
  success: boolean;
  tenant_id: string;
  stats: DocumentStats;
}

export interface UploadInitResponse {
  success: boolean;
  document_id: string;
  storage_key: string;
  upload_url: string;
  expires_at: string;
  processing_status: string;
}

export function useDocumentsApi() {
  const store = useDocumentStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const cancelledRef = useRef(false);

  useEffect(() => {
    return () => { cancelledRef.current = true; };
  }, []);

  const buildQueryParams = useCallback((filters: DocumentFilters, page: number, limit: number) => {
    const params: Record<string, string> = {
      page: String(page),
      limit: String(limit),
      sort_by: filters.sort_by,
      sort_order: filters.sort_order,
      is_archived: String(filters.is_archived),
    };

    if (filters.search) params.search = filters.search;
    if (filters.status.length) params.status = filters.status.join(',');
    if (filters.file_type.length) params.file_type = filters.file_type.join(',');
    if (filters.folder) params.folder = filters.folder;
    if (filters.tags.length) params.tags = filters.tags.join(',');
    if (filters.date_from) params.date_from = filters.date_from;
    if (filters.date_to) params.date_to = filters.date_to;

    return params;
  }, []);

  const fetchDocuments = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const { filters, pagination } = store;
      const params = buildQueryParams(filters, pagination.page, pagination.limit);

      const res = await api.get<DocumentListResponse>('/api/v1/documents/list', { params });

      store.setDocuments(res.documents);
      store.setPagination({
        total: res.total,
        pages: res.pages,
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch documents';
      setError(msg);
      store.setError(msg);
    } finally {
      setLoading(false);
    }
  }, [store, buildQueryParams]);

  const fetchStats = useCallback(async () => {
    try {
      const res = await api.get<DocumentStatsResponse>('/api/v1/documents/stats');
      store.setStats(res.stats);
    } catch {
    }
  }, [store]);

  const deleteDocument = useCallback(async (documentId: string, permanently = false) => {
    setLoading(true);
    setError(null);

    try {
      await api.delete(`/api/v1/documents/${documentId}?permanently=${permanently}`);
      store.removeDocument(documentId);
      await fetchStats();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to delete document';
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [store, fetchStats]);

  const retryDocuments = useCallback(async (documentIds: string[]) => {
    setLoading(true);
    setError(null);

    try {
      const res = await api.post<{ retried_count: number; skipped_count: number }>(
        '/api/v1/documents/retry',
        { document_ids: documentIds }
      );

      for (const id of documentIds) {
        const row = store.documents.find((d) => d.id === id);
        store.updateDocument(id, {
          processing_status: 'retrying',
          retry_count: (row?.retry_count ?? 0) + 1,
        });
      }

      return res;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to retry';
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [store]);

  const updateDocument = useCallback(async (documentId: string, data: Record<string, unknown>) => {
    setLoading(true);
    setError(null);

    try {
      const res = await api.patch<{ success: boolean; document: Document }>(
        `/api/v1/documents/${documentId}`,
        data
      );
      const doc = unwrapDocumentPayload(res);
      store.updateDocument(documentId, doc);
      return doc;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to update document';
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [store]);

  const batchArchive = useCallback(async (documentIds: string[]) => {
    setLoading(true);
    setError(null);
    const previous = documentIds.map((id) => store.documents.find((d) => d.id === id)).filter(Boolean);

    try {
      const res = await api.post<{ updated_count: number; errors?: string[] }>('/api/v1/documents/batch', {
        document_ids: documentIds,
        status: 'archived',
      });

      await fetchDocuments();
      store.clearSelection();

      if (res.errors?.length) {
        const msg = `Archived ${res.updated_count} of ${documentIds.length}. ${res.errors.join(' ')}`;
        setError(msg);
        appToast.warning(msg);
        return;
      }
      appToast.success(`Archived ${res.updated_count} document(s).`);
    } catch (err: unknown) {
      for (const doc of previous) {
        if (doc) store.updateDocument(doc.id, doc);
      }
      const msg = err instanceof Error ? err.message : 'Failed to archive';
      setError(msg);
      appToast.error(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [store, fetchDocuments]);

  const batchRestore = useCallback(async (documentIds: string[]) => {
    setLoading(true);
    setError(null);

    try {
      const res = await api.post<{ updated_count: number; errors?: string[] }>('/api/v1/documents/batch', {
        document_ids: documentIds,
        status: 'restored',
      });

      await fetchDocuments();
      store.clearSelection();

      if (res.errors?.length) {
        const msg = `Restored ${res.updated_count} of ${documentIds.length}. ${res.errors.join(' ')}`;
        setError(msg);
        appToast.warning(msg);
        return;
      }
      appToast.success(`Restored ${res.updated_count} document(s).`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to restore';
      setError(msg);
      appToast.error(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [store, fetchDocuments]);

  const batchDelete = useCallback(async (documentIds: string[]) => {
    setLoading(true);
    setError(null);

    try {
      const res = await api.post<{ updated_count: number; errors?: string[] }>('/api/v1/documents/batch', {
        document_ids: documentIds,
        status: 'deleted',
      });

      await fetchDocuments();
      store.clearSelection();
      await fetchStats();

      if (res.errors?.length) {
        const msg = `Deleted ${res.updated_count} of ${documentIds.length}. ${res.errors.join(' ')}`;
        setError(msg);
        appToast.warning(msg);
        return;
      }
      appToast.success(`Deleted ${res.updated_count} document(s).`);
    } catch (err: unknown) {
      await fetchDocuments();
      const msg = err instanceof Error ? err.message : 'Failed to delete';
      setError(msg);
      appToast.error(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [store, fetchDocuments, fetchStats]);

  const delay = useCallback((ms: number) => {
    return new Promise<void>((resolve) => {
      if (cancelledRef.current) { resolve(); return; }
      const timer = setTimeout(() => {
        if (!cancelledRef.current) resolve();
      }, ms);
      const interval = setInterval(() => {
        if (cancelledRef.current) {
          clearTimeout(timer);
          clearInterval(interval);
          resolve();
        }
      }, 100);
    });
  }, []);

  const pollDocumentStatus = useCallback(async (documentId: string, maxAttempts = 30, intervalMs = 3000) => {
    const poll = async (attempt = 0): Promise<DocumentStatus> => {
      if (cancelledRef.current) {
        throw new PollingCancelledError('Document processing');
      }
      if (attempt >= maxAttempts) {
        throw new PollingTimeoutError('Document processing', maxAttempts, intervalMs);
      }

      try {
        const res = await api.get<{ success: boolean; document: { processing_status: string } }>(
          `/api/v1/documents/${documentId}`
        );
        const status = (res as { document: { processing_status: string } }).document.processing_status;
        store.updateDocument(documentId, { processing_status: status as never });

        if (status === 'completed' || status === 'failed' || status === 'needs_review') {
          return status as never;
        }

        await delay(intervalMs);
        return poll(attempt + 1);
      } catch (err) {
        if (cancelledRef.current) throw new PollingCancelledError('Document processing');
        if (attempt + 1 >= maxAttempts) {
          throw err instanceof PollingTimeoutError ? err : new PollingTimeoutError('Document processing', maxAttempts, intervalMs);
        }
        await delay(intervalMs);
        return poll(attempt + 1);
      }
    };

    try {
      return await poll();
    } catch (err) {
      const msg = formatPollingError(err, 'Document processing');
      setError(msg);
      throw err;
    }
  }, [store, delay]);

  return {
    loading,
    error,
    stats: store.stats,
    fetchDocuments,
    fetchStats,
    deleteDocument,
    retryDocuments,
    updateDocument,
    batchArchive,
    batchRestore,
    batchDelete,
    pollDocumentStatus,
  };
}