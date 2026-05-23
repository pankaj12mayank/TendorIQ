import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import {
  parsePaginated,
  unwrapData,
  type ApiEnvelope,
} from '@/lib/api-envelope';
import {
  mapTenderFromApi,
  mapTenderToApi,
  type ApiTender,
  type ClientTender,
} from '@tendoriq/shared/tenders';
import { type QueryParams, type PaginatedResponse } from '@/lib/query-client';
import { getQueryErrorMessage } from '@/lib/query-error-message';
import { toast } from 'sonner';

export { getQueryErrorMessage } from '@/lib/query-error-message';

export function useApiQuery<T>(key: string[], queryFn: () => Promise<T>, options?: {
  enabled?: boolean;
  staleTime?: number;
}) {
  const query = useQuery({
    queryKey: key,
    queryFn,
    enabled: options?.enabled,
    staleTime: options?.staleTime,
    throwOnError: false,
    retry: 1,
  });
  return {
    ...query,
    errorMessage: getQueryErrorMessage(query.error),
  };
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

export type Tender = ClientTender;

export function useTenders(params?: QueryParams) {
  const query = useQuery({
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
    throwOnError: false,
    retry: 1,
  });
  return {
    ...query,
    errorMessage: getQueryErrorMessage(query.error),
  };
}

export function useTender(id: string) {
  const query = useQuery({
    queryKey: ['tender', id],
    queryFn: async () => {
      const raw = await api.get<ApiEnvelope<ApiTender>>(`/api/v1/tenders/${id}`);
      return mapTenderFromApi(unwrapData(raw));
    },
    enabled: !!id,
    throwOnError: false,
    retry: 1,
  });
  return {
    ...query,
    errorMessage: getQueryErrorMessage(query.error),
  };
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
