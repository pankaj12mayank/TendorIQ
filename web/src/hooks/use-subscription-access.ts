'use client';

import { useQuery } from '@tanstack/react-query';

import { api } from '@/lib/api-client';
import { unwrapData } from '@/lib/api-envelope';
import { useCurrentUser } from '@/hooks/use-auth';

export interface SubscriptionAccess {
  can_use_system: boolean;
  is_expired: boolean;
  plan: string;
  status: string;
  reason: string;
  upgrade_required: boolean;
  period_end?: string | null;
}

export function useSubscriptionAccess() {
  const user = useCurrentUser();
  return useQuery({
    queryKey: ['subscription-access', user?.id],
    queryFn: async () => {
      const raw = await api.get<{ data?: SubscriptionAccess } | SubscriptionAccess>(
        '/api/v1/billing/access-status'
      );
      return unwrapData(raw as { data?: SubscriptionAccess }) as SubscriptionAccess;
    },
    enabled: Boolean(user?.id),
    refetchInterval: 60_000,
  });
}
