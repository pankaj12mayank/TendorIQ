/**
 * Normalizes TenderIQ API envelopes (`{ success, data, meta }`) for the web app.
 */

export interface ApiEnvelope<T = unknown> {
  success?: boolean;
  data?: T;
  meta?: Record<string, unknown>;
  error?: unknown;
}

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
}

export interface PaginatedResult<T> {
  data: T[];
  meta: PaginationMeta;
}

function toIso(value: unknown): string | null {
  if (value == null) return null;
  if (typeof value === 'string') return value;
  if (value instanceof Date) return value.toISOString();
  return String(value);
}

export function unwrapData<T>(payload: ApiEnvelope<T> | T): T {
  if (payload && typeof payload === 'object' && 'data' in (payload as ApiEnvelope<T>)) {
    const envelope = payload as ApiEnvelope<T>;
    if (envelope.data !== undefined && envelope.data !== null) {
      return envelope.data;
    }
  }
  return payload as T;
}

export function parsePaginationMeta(meta?: Record<string, unknown>): PaginationMeta {
  const page = Number(meta?.page ?? 1);
  const limit = Number(meta?.limit ?? 20);
  const total = Number(meta?.total ?? 0);
  const totalPages = Number(meta?.totalPages ?? meta?.total_pages ?? 0);
  return {
    page,
    limit,
    total,
    totalPages: totalPages || (limit > 0 ? Math.ceil(total / limit) : 0),
  };
}

export function parsePaginated<T>(
  payload: ApiEnvelope<T[]> | PaginatedResult<T>
): PaginatedResult<T> {
  if (payload && typeof payload === 'object' && 'data' in payload && Array.isArray((payload as PaginatedResult<T>).data)) {
    const direct = payload as PaginatedResult<T>;
    if (direct.meta?.totalPages !== undefined) {
      return direct;
    }
  }
  const envelope = payload as ApiEnvelope<T[]>;
  return {
    data: (unwrapData(envelope) ?? []) as T[],
    meta: parsePaginationMeta(envelope.meta),
  };
}

export interface ApiTender {
  id: string;
  title: string;
  description?: string;
  status: string;
  budget?: number | null;
  currency?: string;
  closingDate?: string | null;
  closing_date?: string | null;
  organizationId?: string;
  organization_id?: string;
  tenant_id?: string;
  createdAt?: string;
  created_at?: string;
  updatedAt?: string;
  updated_at?: string;
}

export function mapTenderFromApi(raw: ApiTender): {
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
} {
  const status = (raw.status || 'draft') as 'draft' | 'published' | 'closed' | 'cancelled' | 'awarded';
  const org =
    raw.organizationId ??
    raw.organization_id ??
    (raw.tenant_id != null ? String(raw.tenant_id) : '');
  return {
    id: String(raw.id),
    title: raw.title ?? '',
    description: raw.description ?? '',
    status,
    budget: raw.budget ?? null,
    currency: raw.currency ?? 'USD',
    closingDate: toIso(raw.closingDate ?? raw.closing_date),
    organizationId: org,
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

/** Display helpers for tender list cards */
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
