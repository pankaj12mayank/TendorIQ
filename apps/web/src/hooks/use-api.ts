import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import { type QueryParams, type PaginatedResponse } from '@/lib/query-client';
import { toast } from '@/stores/toast-store';

export function useApiQuery<T>(key: string[], queryFn: () => Promise<T>, options?: {
  enabled?: boolean;
  staleTime?: number;
}) {
  return useQuery({
    queryKey: key,
    queryFn,
    enabled: options?.enabled,
    staleTime: options?.staleTime,
    throwOnError: false,
  });
}

export function useApiMutation<TData, TVariables>(
  key: string[],
  mutationFn: (variables: TVariables) => Promise<TData>,
  options?: {
    onSuccess?: (data: TData) => void;
    onError?: (error: Error) => void;
    invalidate?: string[];
  }
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn,
    onSuccess: (data) => {
      if (options?.invalidate) {
        options.invalidate.forEach((key) => {
          queryClient.invalidateQueries({ queryKey: [key] });
        });
      }
      options?.onSuccess?.(data);
    },
    onError: (error: Error) => {
      toast.error('Operation failed', error.message);
      options?.onError?.(error);
    },
  });
}

export interface Tender {
  id: string;
  title: string;
  description: string;
  status: 'draft' | 'published' | 'closed' | 'cancelled' | 'awarded';
  budget: number | null;
  currency: string;
  closingDate: string | null;
  organizationId: string;
  createdAt: string;
  updatedAt: string;
}

export function useTenders(params?: QueryParams) {
  return useQuery({
    queryKey: ['tenders', params],
    queryFn: () =>
      api.get<PaginatedResponse<Tender>>('/api/v1/tenders', { params: params as Record<string, string> }),
  });
}

export function useTender(id: string) {
  return useQuery({
    queryKey: ['tender', id],
    queryFn: () => api.get<Tender>(`/api/v1/tenders/${id}`),
    enabled: !!id,
  });
}

export function useCreateTender() {
  return useApiMutation(
    ['tenders'],
    (data: Partial<Tender>) => api.post<Tender>('/api/v1/tenders', data),
    { invalidate: ['tenders'] }
  );
}

export function useUpdateTender() {
  return useApiMutation(
    ['tenders'],
    ({ id, ...data }: Partial<Tender> & { id: string }) =>
      api.patch<Tender>(`/api/v1/tenders/${id}`, data),
    { invalidate: ['tenders', 'tender'] }
  );
}

export function useDeleteTender() {
  return useApiMutation(
    ['tenders'],
    (id: string) => api.delete(`/api/v1/tenders/${id}`),
    { invalidate: ['tenders'] }
  );
}