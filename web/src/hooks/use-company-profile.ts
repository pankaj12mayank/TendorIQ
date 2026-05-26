import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { api } from '@/lib/api-client';
import { unwrapData } from '@/lib/api-envelope';
import { useCurrentUser } from '@/hooks/use-auth';

export interface CompanyProfile {
  id?: string;
  user_id?: string;
  company_name?: string | null;
  industry?: string | null;
  address?: string | null;
  phone?: string | null;
  website?: string | null;
  tax_id?: string | null;
  logo_url?: string | null;
}

export function useCompanyProfile() {
  const user = useCurrentUser();
  return useQuery({
    queryKey: ['company-profile', user?.id],
    queryFn: async () => {
      const raw = await api.get<{ data?: CompanyProfile } | CompanyProfile>(
        '/api/v1/auth/me/company-profile'
      );
      return unwrapData(raw as { data?: CompanyProfile }) as CompanyProfile;
    },
    enabled: Boolean(user?.id),
  });
}

export function useUpdateCompanyProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: Partial<CompanyProfile>) => {
      const raw = await api.patch<{ data?: CompanyProfile } | CompanyProfile>(
        '/api/v1/auth/me/company-profile',
        body
      );
      return unwrapData(raw as { data?: CompanyProfile }) as CompanyProfile;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['company-profile'] });
    },
  });
}
