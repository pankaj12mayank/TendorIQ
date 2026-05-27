import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';

export type DocumentStatus = 'uploaded' | 'processing' | 'retrying' | 'completed' | 'failed' | 'needs_review' | 'deleted';

export interface Document {
  id: string;
  name: string;
  file_name: string;
  file_type: string;
  file_size: number;
  mime_type?: string;
  processing_status: DocumentStatus;
  retry_count: number;
  folder?: string;
  tags: string[];
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface DocumentFilters {
  search: string;
  status: DocumentStatus[];
  file_type: string[];
  folder: string;
  tags: string[];
  is_archived: boolean;
  date_from: string;
  date_to: string;
  sort_by: 'created_at' | 'file_name' | 'file_size' | 'file_type';
  sort_order: 'asc' | 'desc';
}

export interface DocumentStats {
  total_documents: number;
  total_size_bytes: number;
  total_size_mb: number;
  by_status: Record<string, number>;
  by_type: Record<string, number>;
  failed_count: number;
  needs_review_count: number;
  pending_count: number;
  quota_usage_percent: number;
}

interface DocumentState {
  documents: Document[];
  selectedDocuments: string[];
  filters: DocumentFilters;
  pagination: {
    page: number;
    limit: number;
    total: number;
    pages: number;
  };
  stats: DocumentStats | null;
  isLoading: boolean;
  error: string | null;

  setDocuments: (docs: Document[]) => void;
  addDocument: (doc: Document) => void;
  updateDocument: (id: string, updates: Partial<Document>) => void;
  removeDocument: (id: string) => void;
  setSelectedDocuments: (ids: string[]) => void;
  toggleSelect: (id: string) => void;
  selectAll: () => void;
  clearSelection: () => void;

  setFilters: (filters: Partial<DocumentFilters>) => void;
  resetFilters: () => void;
  setPage: (page: number) => void;
  setLimit: (limit: number) => void;
  setPagination: (pagination: Partial<DocumentState['pagination']>) => void;
  setStats: (stats: DocumentStats) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

const initialFilters: DocumentFilters = {
  search: '',
  status: [],
  file_type: [],
  folder: '',
  tags: [],
  is_archived: false,
  date_from: '',
  date_to: '',
  sort_by: 'created_at',
  sort_order: 'desc',
};

const initialPagination = {
  page: 1,
  limit: 20,
  total: 0,
  pages: 0,
};

export const useDocumentStore = create<DocumentState>()(
  persist(
    (set) => ({
  documents: [],
  selectedDocuments: [],
  filters: initialFilters,
  pagination: initialPagination,
  stats: null,
  isLoading: false,
  error: null,

  setDocuments: (docs) => set({ documents: docs }),

  addDocument: (doc) => set((state) => ({
    documents: [doc, ...state.documents],
    pagination: { ...state.pagination, total: state.pagination.total + 1 },
  })),

  updateDocument: (id, updates) => set((state) => ({
    documents: state.documents.map((d) => d.id === id ? { ...d, ...updates } : d),
  })),

  removeDocument: (id) => set((state) => ({
    documents: state.documents.filter((d) => d.id !== id),
    selectedDocuments: state.selectedDocuments.filter((sid) => sid !== id),
    pagination: { ...state.pagination, total: Math.max(0, state.pagination.total - 1) },
  })),

  setSelectedDocuments: (ids) => set({ selectedDocuments: ids }),

  toggleSelect: (id) => set((state) => ({
    selectedDocuments: state.selectedDocuments.includes(id)
      ? state.selectedDocuments.filter((sid) => sid !== id)
      : [...state.selectedDocuments, id],
  })),

  selectAll: () => set((state) => ({
    selectedDocuments: state.documents.map((d) => d.id),
  })),

  clearSelection: () => set({ selectedDocuments: [] }),

  setFilters: (filters) => set((state) => ({
    filters: { ...state.filters, ...filters },
    pagination: { ...state.pagination, page: 1 },
  })),

  resetFilters: () => set({ filters: initialFilters, pagination: { ...initialPagination } }),

  setPage: (page) => set((state) => ({ pagination: { ...state.pagination, page } })),
  setLimit: (limit) => set((state) => ({ pagination: { ...state.pagination, limit, page: 1 } })),
  setPagination: (pagination) => set((state) => ({ pagination: { ...state.pagination, ...pagination } })),
  setStats: (stats) => set({ stats }),
  setLoading: (loading) => set({ isLoading: loading }),
      setError: (error) => set({ error }),
    }),
    {
      name: 'tendoriq-documents-ui',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        filters: state.filters,
        pagination: {
          page: state.pagination.page,
          limit: state.pagination.limit,
        },
      }),
      merge: (persisted, current) => ({
        ...current,
        ...(persisted as Partial<DocumentState>),
        pagination: {
          ...current.pagination,
          ...(persisted as Partial<DocumentState>)?.pagination,
          total: 0,
          pages: 0,
        },
      }),
    }
  )
);