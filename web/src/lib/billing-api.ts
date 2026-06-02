import type {
  Plan,
  Subscription,
  QuotaStatus,
  Invoice,
  PaymentMethod,
} from '@/components/billing/types';
import type { QuotaStatus as UsageQuotaStatus, UsageSummary as TenantUsageSummary } from '@/components/usage/types';
import { unwrapData, type ApiEnvelope } from '@/lib/api-envelope';

/** API plan prices are already in cents (matches formatCurrency). */
export function mapPlansFromApi(raw: Plan[]): Plan[] {
  return raw;
}

export function parsePlansResponse(payload: unknown): Plan[] {
  if (Array.isArray(payload)) return mapPlansFromApi(payload);
  const unwrapped = unwrapData<Plan[] | { plans?: Plan[] }>(payload as ApiEnvelope<Plan[] | { plans?: Plan[] }>);
  if (Array.isArray(unwrapped)) return mapPlansFromApi(unwrapped);
  const body = payload as { plans?: Plan[] };
  return mapPlansFromApi(body.plans ?? (unwrapped as { plans?: Plan[] })?.plans ?? []);
}

export function mapSubscriptionFromApi(raw: unknown): Subscription {
  return unwrapData(raw as Subscription) as Subscription;
}

export function mapQuotaFromUsageApi(res: unknown): QuotaStatus[] {
  const body = (unwrapData(res) ?? res) as { quota?: QuotaStatus[]; quotas?: QuotaStatus[] };
  return body.quotas ?? body.quota ?? [];
}

export function mapUsageQuotas(res: unknown): UsageQuotaStatus[] {
  const body = (unwrapData(res) ?? res) as { quota?: UsageQuotaStatus[]; quotas?: UsageQuotaStatus[] };
  return body.quotas ?? body.quota ?? [];
}

export function mapUsageSummary(res: unknown): TenantUsageSummary {
  return unwrapData(res as TenantUsageSummary) as TenantUsageSummary;
}

export function parseInvoicesResponse(payload: unknown): Invoice[] {
  const body = payload as { invoices?: Invoice[]; data?: Invoice[] };
  if (Array.isArray(body.invoices)) return body.invoices;
  const unwrapped = unwrapData<Invoice[]>(payload as { data?: Invoice[] });
  return Array.isArray(unwrapped) ? unwrapped : [];
}

export function parsePaymentMethodsResponse(payload: unknown): PaymentMethod[] {
  const body = payload as { payment_methods?: PaymentMethod[]; data?: PaymentMethod[] };
  if (Array.isArray(body.payment_methods)) return body.payment_methods;
  const unwrapped = unwrapData<PaymentMethod[]>(payload as { data?: PaymentMethod[] });
  return Array.isArray(unwrapped) ? unwrapped : [];
}
