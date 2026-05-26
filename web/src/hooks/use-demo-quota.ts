'use client';

import { useQuery } from '@tanstack/react-query';

import { api } from '@/lib/api-client';
import { unwrapData } from '@/lib/api-envelope';
import { useCurrentUser } from '@/hooks/use-auth';

export interface DemoUsageRow {
  operation: string;
  featureKey: string;
  used: number;
  limit: number | null;
  remaining: number | null;
  isExceeded: boolean;
}

export interface DemoStatus {
  plan: string;
  is_demo: boolean;
  usage: DemoUsageRow[];
  ai_tokens: { used: number; limit: number | null };
}

export function useDemoStatus() {
  const user = useCurrentUser();
  return useQuery({
    queryKey: ['demo-status', user?.id],
    queryFn: async () => {
      const raw = await api.get<{ data?: DemoStatus } | DemoStatus>('/api/v1/billing/demo-status');
      return unwrapData(raw as { data?: DemoStatus }) as DemoStatus;
    },
    enabled: Boolean(user?.id),
    refetchInterval: 60_000,
  });
}
