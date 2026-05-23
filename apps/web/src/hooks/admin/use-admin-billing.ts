import { useCallback, useState } from 'react';
import { toast } from 'sonner';

import { api, ApiError } from '@/lib/api-client';
import { ADMIN_PLATFORM_PATHS } from '@/lib/admin-platform-paths';
import { BillingPlan } from '@/components/admin/types';

import { reportAdminApiError } from './admin-api-errors';

/** Platform billing overview — not tenant `useBillingApi` in `@/hooks/use-billing`. */
export function useAdminBillingApi() {
  const [plans, setPlans] = useState<BillingPlan[]>([]);
  const [subscriptions, setSubscriptions] = useState<unknown[]>([]);
  const [isLoading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchBilling = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get<{
        plans: BillingPlan[];
        subscriptions: unknown[];
        invoices: unknown[];
      }>(ADMIN_PLATFORM_PATHS.billing);
      setPlans(res.plans);
      setSubscriptions(res.subscriptions);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to load billing');
      reportAdminApiError(err, 'Billing data could not be loaded');
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    plans,
    subscriptions,
    isLoading,
    error,
    fetchBilling,
    createPlan: async () => {
      toast.info('Plan changes are managed in billing configuration');
    },
    updatePlan: async () => {
      toast.info('Plan changes are managed in billing configuration');
    },
    deletePlan: async () => {
      toast.info('Plan changes are managed in billing configuration');
    },
  };
}

/** @deprecated Use `useAdminBillingApi` — kept for admin modules importing `useBillingApi`. */
export const useBillingApi = useAdminBillingApi;
