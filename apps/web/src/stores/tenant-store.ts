import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface Organization {
  id: string;
  name: string;
  slug: string;
  logo?: string;
  role: 'admin' | 'manager' | 'member' | 'viewer';
}

interface TenantState {
  currentOrganization: Organization | null;
  organizations: Organization[];
  isLoading: boolean;
  setCurrentOrganization: (org: Organization | null) => void;
  setOrganizations: (orgs: Organization[]) => void;
  setLoading: (loading: boolean) => void;
}

export const useTenantStore = create<TenantState>()(
  persist(
    (set) => ({
      currentOrganization: null,
      organizations: [],
      isLoading: false,
      setCurrentOrganization: (org) => set({ currentOrganization: org }),
      setOrganizations: (orgs) => set({ organizations: orgs }),
      setLoading: (isLoading) => set({ isLoading }),
    }),
    {
      name: 'tenant-storage',
      partialize: (state) => ({
        currentOrganization: state.currentOrganization,
        organizations: state.organizations,
      }),
    }
  )
);