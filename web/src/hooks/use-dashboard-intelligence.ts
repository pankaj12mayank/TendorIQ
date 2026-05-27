'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { authenticatedJson } from '@/lib/api-fetch';
import type { PipelineStep } from '@/components/design-system/ai-pipeline';

const STALE_MS = 30_000;
const PIPELINE_POLL_MS = 8_000;

export type DashboardOverview = {
  uploads_today: number;
  active_users: number;
  inactive_users: number;
  revenue: number;
  failed_ai_jobs: number;
  recent_payments: {
    id: string;
    provider: string;
    amount: number;
    currency: string;
    plan?: string | null;
    status: string;
    user_email: string;
    created_at: string | null;
  }[];
  generated_at: string;
};

export type PipelineJob = {
  document_id: string;
  document_name: string;
  tender_id: string | null;
  tender_title: string | null;
  owner_email: string;
  owner_name: string;
  processing_status: string;
  updated_at: string;
  pipeline: {
    stages: PipelineStep[];
    current_stage: string | null;
    processing_status: string;
    is_terminal: boolean;
    is_failed: boolean;
    is_retrying: boolean;
    retry_count: number;
  };
};

export type PipelineListParams = {
  page?: number;
  limit?: number;
};

export type DashboardTender = {
  id: string;
  title: string;
  status: string;
  owner_id: string | null;
  owner_email: string;
  budget?: number | null;
  currency?: string;
  created_at: string;
};

export type RegisteredUserRow = {
  id: string;
  name: string;
  email: string;
  status: string;
  plan: string;
  role: string;
  organization: string;
  last_active: string | null;
  usage: { uploads: number; analysis: number; proposals: number };
};

export type TenderListParams = {
  page?: number;
  limit?: number;
  status?: string;
  user_id?: string;
  search?: string;
};

export type UserListParams = {
  page?: number;
  limit?: number;
  status?: string;
  plan?: string;
  search?: string;
};

function qs(params: Record<string, string | number | undefined>) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && String(v) !== '') search.set(k, String(v));
  });
  return search.toString();
}

export function useDashboardOverview() {
  return useQuery({
    queryKey: ['dashboard', 'overview'],
    queryFn: async () => {
      const res = await authenticatedJson<{ data: DashboardOverview }>(
        '/api/v1/admin/platform/dashboard/overview'
      );
      return res.data;
    },
    staleTime: STALE_MS,
  });
}

export function useDashboardPipeline(params?: PipelineListParams) {
  const page = params?.page ?? 1;
  const limit = params?.limit ?? 12;
  const query = useQuery({
    queryKey: ['dashboard', 'pipeline', page, limit],
    queryFn: async () => {
      const res = await authenticatedJson<{
        data: { jobs: PipelineJob[]; has_active: boolean; generated_at: string };
        pagination: { page: number; limit: number; total: number; pages: number };
      }>(`/api/v1/admin/platform/dashboard/pipeline?page=${page}&limit=${limit}`);
      return { ...res.data, pagination: res.pagination };
    },
    staleTime: 5_000,
    refetchInterval: (q) => (q.state.data?.has_active ? PIPELINE_POLL_MS : false),
  });
  return query;
}

export function useDashboardTenders(params: TenderListParams) {
  const queryString = qs({
    page: params.page ?? 1,
    limit: params.limit ?? 10,
    status: params.status,
    user_id: params.user_id,
    search: params.search,
  });
  return useQuery({
    queryKey: ['dashboard', 'tenders', params],
    queryFn: async () => {
      const res = await authenticatedJson<{
        data: DashboardTender[];
        pagination: { page: number; limit: number; total: number; pages: number };
      }>(`/api/v1/admin/platform/dashboard/tenders?${queryString}`);
      return { items: res.data ?? [], pagination: res.pagination };
    },
    staleTime: STALE_MS,
  });
}

export function useDashboardRegisteredUsers(params: UserListParams) {
  const queryString = qs({
    page: params.page ?? 1,
    limit: params.limit ?? 8,
    status: params.status,
    plan: params.plan,
    search: params.search,
  });
  return useQuery({
    queryKey: ['dashboard', 'users', params],
    queryFn: async () => {
      const res = await authenticatedJson<{
        data: {
          summary: {
            active_users: number;
            inactive_users: number;
            by_plan: Record<string, number>;
          };
          users: RegisteredUserRow[];
        };
        pagination: { page: number; limit: number; total: number; pages: number };
      }>(`/api/v1/admin/platform/dashboard/users?${queryString}`);
      return {
        summary: res.data.summary,
        users: res.data.users ?? [],
        pagination: res.pagination,
      };
    },
    staleTime: STALE_MS,
  });
}

export function useDashboardUserOptions(search?: string) {
  const queryString = qs({ q: search, limit: 25 });
  return useQuery({
    queryKey: ['dashboard', 'user-options', search ?? ''],
    queryFn: async () => {
      const res = await authenticatedJson<{
        data: { id: string; email: string; name: string }[];
      }>(`/api/v1/admin/platform/dashboard/user-options?${queryString}`);
      return res.data ?? [];
    },
    staleTime: 15_000,
  });
}

export function useDeleteDashboardTender() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (tenderId: string) => {
      await authenticatedJson(`/api/v1/admin/platform/dashboard/tenders/${tenderId}`, {
        method: 'DELETE',
      });
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['dashboard', 'tenders'] });
      void queryClient.invalidateQueries({ queryKey: ['dashboard', 'overview'] });
    },
  });
}
