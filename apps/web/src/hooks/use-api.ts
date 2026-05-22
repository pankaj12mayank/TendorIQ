import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import {
  mapTenderFromApi,
  mapTenderToApi,
  parsePaginated,
  unwrapData,
  type ApiEnvelope,
  type ApiTender,
} from '@/lib/api-envelope';
import { type QueryParams, type PaginatedResponse } from '@/lib/query-client';
import { toast } from 'sonner';

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
      toast.error(`Operation failed: ${error.message}`);
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
    queryFn: async () => {
      const raw = await api.get<ApiEnvelope<ApiTender[]>>('/api/v1/tenders', {
        params: params as Record<string, string>,
      });
      const page = parsePaginated(raw);
      return {
        data: page.data.map(mapTenderFromApi),
        meta: page.meta,
      } satisfies PaginatedResponse<Tender>;
    },
  });
}

export function useTender(id: string) {
  return useQuery({
    queryKey: ['tender', id],
    queryFn: async () => {
      const raw = await api.get<ApiEnvelope<ApiTender>>(`/api/v1/tenders/${id}`);
      return mapTenderFromApi(unwrapData(raw));
    },
    enabled: !!id,
  });
}

export function useCreateTender() {
  return useApiMutation(
    ['tenders'],
    async (data: Partial<Tender>) => {
      const raw = await api.post<ApiEnvelope<ApiTender>>(
        '/api/v1/tenders',
        mapTenderToApi(data)
      );
      return mapTenderFromApi(unwrapData(raw));
    },
    { invalidate: ['tenders'] }
  );
}

export function useUpdateTender() {
  return useApiMutation(
    ['tenders'],
    async ({ id, ...data }: Partial<Tender> & { id: string }) => {
      const raw = await api.patch<ApiEnvelope<ApiTender>>(
        `/api/v1/tenders/${id}`,
        mapTenderToApi(data)
      );
      return mapTenderFromApi(unwrapData(raw));
    },
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
