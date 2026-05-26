/**
 * Tender API ↔ client field mapping (tenant-scoped; no separate organization column).
 */

export interface ApiTender {
  id: string;
  title: string;
  description?: string;
  status: string;
  budget?: number | null;
  currency?: string;
  closingDate?: string | null;
  closing_date?: string | null;
  tenantId?: string;
  tenant_id?: string;
  /** @deprecated Use tenantId — kept for legacy API payloads */
  organizationId?: string;
  organization_id?: string;
  createdAt?: string;
  created_at?: string;
  updatedAt?: string;
  updated_at?: string;
}

export interface ClientTender {
  id: string;
  title: string;
  description: string;
  status: 'draft' | 'published' | 'closed' | 'cancelled' | 'awarded';
  budget: number | null;
  currency: string;
  closingDate: string | null;
  tenantId: string;
  /** @deprecated Alias of tenantId for older UI code */
  organizationId: string;
  createdAt: string;
  updatedAt: string;
}

function toIso(value: string | null | undefined): string | null {
  if (!value) return null;
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? null : d.toISOString();
}

export function mapTenderFromApi(raw: ApiTender): ClientTender {
  const status = (raw.status || 'draft') as ClientTender['status'];
  const tenantId =
    raw.tenantId ??
    raw.tenant_id ??
    raw.organizationId ??
    raw.organization_id ??
    '';
  return {
    id: String(raw.id),
    title: raw.title ?? '',
    description: raw.description ?? '',
    status,
    budget: raw.budget ?? null,
    currency: raw.currency ?? 'USD',
    closingDate: toIso(raw.closingDate ?? raw.closing_date),
    tenantId,
    organizationId: tenantId,
    createdAt: toIso(raw.createdAt ?? raw.created_at) ?? new Date().toISOString(),
    updatedAt: toIso(raw.updatedAt ?? raw.updated_at) ?? new Date().toISOString(),
  };
}

export function mapTenderToApi(
  input: Partial<{
    title: string;
    description: string;
    status: string;
    budget: number | null;
    currency: string;
    closingDate: string | null;
  }>
): Record<string, unknown> {
  const body: Record<string, unknown> = {};
  if (input.title !== undefined) body.title = input.title;
  if (input.description !== undefined) body.description = input.description;
  if (input.status !== undefined) body.status = input.status;
  if (input.budget !== undefined) body.budget = input.budget;
  if (input.currency !== undefined) body.currency = input.currency;
  if (input.closingDate !== undefined) body.closing_date = input.closingDate;
  return body;
}

export function formatTenderDeadline(tender: { closingDate?: string | null }): string {
  if (!tender.closingDate) return '—';
  try {
    return new Date(tender.closingDate).toLocaleDateString();
  } catch {
    return '—';
  }
}

export function formatTenderValue(tender: { budget?: number | null; currency?: string }): string {
  if (tender.budget == null) return '—';
  const cur = tender.currency ?? 'USD';
  return new Intl.NumberFormat(undefined, { style: 'currency', currency: cur }).format(tender.budget);
}
