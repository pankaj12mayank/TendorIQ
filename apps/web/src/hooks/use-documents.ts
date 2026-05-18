import { useCallback, useState } from 'react';
import { api } from '@/lib/api';
import { useDocumentStore, Document, DocumentStats, DocumentFilters } from '@/stores/document-store';

export interface DocumentListResponse {
  success: boolean;
  documents: Document[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

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
    } catch (err) {
      console.error('Failed to fetch stats:', err);
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
        store.updateDocument(id, { processing_status: 'retrying', retry_count: 0 });
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
      const res = await api.patch<{ document: Document }>(
        `/api/v1/documents/${documentId}`,
        data
      );
      store.updateDocument(documentId, res.document);
      return res.document;
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

    try {
      await api.post('/api/v1/documents/batch', {
        document_ids: documentIds,
        status: 'archived',
      });

      for (const id of documentIds) {
        store.updateDocument(id, { is_archived: true });
      }
      store.clearSelection();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to archive';
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [store]);

  const batchRestore = useCallback(async (documentIds: string[]) => {
    setLoading(true);
    setError(null);

    try {
      await api.post('/api/v1/documents/batch', {
        document_ids: documentIds,
        status: 'restored',
      });

      for (const id of documentIds) {
        store.updateDocument(id, { is_archived: false });
      }
      store.clearSelection();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to restore';
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [store]);

  const batchDelete = useCallback(async (documentIds: string[]) => {
    setLoading(true);
    setError(null);

    try {
      await api.post('/api/v1/documents/batch', {
        document_ids: documentIds,
        status: 'deleted',
      });

      for (const id of documentIds) {
        store.removeDocument(id);
      }
      store.clearSelection();
      await fetchStats();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to delete';
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [store, fetchStats]);

  const pollDocumentStatus = useCallback(async (documentId: string, maxAttempts = 30, intervalMs = 3000) => {
    let attempts = 0;

    const poll = async (): Promise<DocumentStatus> => {
      if (attempts >= maxAttempts) {
        throw new Error('Polling timeout');
      }

      try {
        const res = await api.get<{ document: { processing_status: string } }>(
          `/api/v1/documents/${documentId}`
        );
        const status = res.document.processing_status as string;
        store.updateDocument(documentId, { processing_status: status as never });

        if (status === 'completed' || status === 'failed' || status === 'needs_review') {
          return status as never;
        }

        attempts++;
        await new Promise((resolve) => setTimeout(resolve, intervalMs));
        return poll();
      } catch (err) {
        attempts++;
        if (attempts >= maxAttempts) throw err;
        await new Promise((resolve) => setTimeout(resolve, intervalMs));
        return poll();
      }
    };

    return poll();
  }, [store]);

  return {
    loading,
    error,
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