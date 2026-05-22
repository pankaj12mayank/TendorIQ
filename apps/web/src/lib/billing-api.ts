import type { Plan, Subscription, QuotaStatus, UsageSummary } from '@/components/billing/types';
import type { QuotaStatus as UsageQuotaStatus, UsageSummary as TenantUsageSummary } from '@/components/usage/types';
import { unwrapData } from '@/lib/api-envelope';

/** API plan prices are already in cents (matches formatCurrency). */
export function mapPlansFromApi(raw: Plan[]): Plan[] {
  return raw;
}

export function mapSubscriptionFromApi(raw: Subscription): Subscription {
  return unwrapData(raw) as Subscription;
}

export function mapQuotaFromUsageApi(res: {
  quota?: QuotaStatus[];
  quotas?: QuotaStatus[];
}): QuotaStatus[] {
  return res.quotas ?? res.quota ?? [];
}

export function mapUsageQuotas(res: { quotas: UsageQuotaStatus[] }): UsageQuotaStatus[] {
  return res.quotas ?? [];
}

export function mapUsageSummary(res: TenantUsageSummary): TenantUsageSummary {
  return unwrapData(res) as TenantUsageSummary;
}
