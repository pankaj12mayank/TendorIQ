import { useQuery } from '@tanstack/react-query';

import { api } from '@/lib/api-client';
import { unwrapData } from '@/lib/api-envelope';
import { DEFAULT_UPLOAD_CONFIG, type UploadConfig } from '@/shared/upload-policy';

export function useUploadConfig() {
  return useQuery({
    queryKey: ['upload-config'],
    queryFn: async (): Promise<UploadConfig> => {
      try {
        const raw = await api.get<{ data?: UploadConfig } | UploadConfig>(
          '/api/v1/files/upload/config'
        );
        const body = unwrapData(raw as { data?: UploadConfig });
        return { ...DEFAULT_UPLOAD_CONFIG, ...body };
      } catch {
        return DEFAULT_UPLOAD_CONFIG;
      }
    },
    staleTime: 60_000,
  });
}
