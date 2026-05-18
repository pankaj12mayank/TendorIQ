import { create } from 'zustand';
import { AdminModule, User, AdvancedFilter, PaginationState, SortState } from './types';
import { MOCK_USERS, MOCK_AUDIT_LOGS, MOCK_QUEUE_JOBS, MOCK_FAILED_JOBS } from './constants';

interface AdminState {
  activeModule: AdminModule;
  users: User[];
  pagination: PaginationState;
  sort: SortState;
  filters: AdvancedFilter[];
  searchQuery: string;
  selectedItems: string[];
  isLoading: boolean;
  isModalOpen: boolean;
  modalType: string | null;

  setActiveModule: (module: AdminModule) => void;
  setUsers: (users: User[]) => void;
  addUser: (user: User) => void;
  updateUser: (id: string, data: Partial<User>) => void;
  deleteUser: (id: string) => void;
  setPagination: (pagination: Partial<PaginationState>) => void;
  setSort: (sort: SortState) => void;
  setFilters: (filters: AdvancedFilter[]) => void;
  addFilter: (filter: AdvancedFilter) => void;
  removeFilter: (field: string) => void;
  clearFilters: () => void;
  setSearchQuery: (query: string) => void;
  toggleSelectItem: (id: string) => void;
  selectAllItems: (ids: string[]) => void;
  clearSelection: () => void;
  setLoading: (loading: boolean) => void;
  openModal: (type: string) => void;
  closeModal: () => void;
}

export const useAdminStore = create<AdminState>((set) => ({
  activeModule: 'users',
  users: MOCK_USERS,
  pagination: { page: 1, pageSize: 10, total: MOCK_USERS.length, totalPages: 3 },
  sort: { field: 'createdAt', direction: 'desc' },
  filters: [],
  searchQuery: '',
  selectedItems: [],
  isLoading: false,
  isModalOpen: false,
  modalType: null,

  setActiveModule: (module) => set({ activeModule: module }),

  setUsers: (users) => set({ users }),

  addUser: (user) => set((state) => ({
    users: [...state.users, user],
    pagination: { ...state.pagination, total: state.pagination.total + 1 },
  })),

  updateUser: (id, data) => set((state) => ({
    users: state.users.map((u) => u.id === id ? { ...u, ...data } : u),
  })),

  deleteUser: (id) => set((state) => ({
    users: state.users.filter((u) => u.id !== id),
    pagination: { ...state.pagination, total: state.pagination.total - 1 },
  })),

  setPagination: (pagination) => set((state) => ({
    pagination: { ...state.pagination, ...pagination },
  })),

  setSort: (sort) => set({ sort }),

  setFilters: (filters) => set({ filters }),

  addFilter: (filter) => set((state) => ({
    filters: [...state.filters.filter((f) => f.field !== filter.field), filter],
  })),

  removeFilter: (field) => set((state) => ({
    filters: state.filters.filter((f) => f.field !== field),
  })),

  clearFilters: () => set({ filters: [] }),

  setSearchQuery: (query) => set({ searchQuery: query }),

  toggleSelectItem: (id) => set((state) => ({
    selectedItems: state.selectedItems.includes(id)
      ? state.selectedItems.filter((i) => i !== id)
      : [...state.selectedItems, id],
  })),

  selectAllItems: (ids) => set({ selectedItems: ids }),

  clearSelection: () => set({ selectedItems: [] }),

  setLoading: (loading) => set({ isLoading: loading }),

  openModal: (type) => set({ isModalOpen: true, modalType: type }),

  closeModal: () => set({ isModalOpen: false, modalType: null }),
}));

interface AnalyticsState {
  metrics: {
    totalUsers: number;
    activeDocuments: number;
    apiCallsToday: number;
    monthlyCost: number;
  };
  sparklineData: {
    users: number[];
    apiCalls: number[];
    cost: number[];
  };

  setMetrics: (metrics: AnalyticsState['metrics']) => void;
  updateMetric: (key: keyof AnalyticsState['metrics'], value: number) => void;
}

export const useAnalyticsStore = create<AnalyticsState>((set) => ({
  metrics: {
    totalUsers: 28,
    activeDocuments: 1247,
    apiCallsToday: 2100,
    monthlyCost: 2847,
  },
  sparklineData: {
    users: [20, 22, 25, 24, 26, 28],
    apiCalls: [1500, 1800, 1600, 2000, 1900, 2100],
    cost: [2200, 2400, 2300, 2700, 2600, 2847],
  },

  setMetrics: (metrics) => set({ metrics }),
  updateMetric: (key, value) => set((state) => ({
    metrics: { ...state.metrics, [key]: value },
  })),
}));