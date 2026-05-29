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

export function parsePaginationMeta(
  meta?: Record<string, unknown>,
  legacy?: { page?: unknown; limit?: unknown; total?: unknown }
): PaginationMeta {
  const page = Number(meta?.page ?? legacy?.page ?? 1);
  const limit = Number(meta?.limit ?? legacy?.limit ?? 20);
  const total = Number(meta?.total ?? legacy?.total ?? 0);
  const totalPages = Number(meta?.totalPages ?? meta?.total_pages ?? 0);
  return {
    page,
    limit,
    total,
    totalPages: totalPages || (limit > 0 ? Math.ceil(total / limit) : 0),
  };
}

/** Extract a human-readable message from API or FastAPI error JSON. */
export function parseApiErrorMessage(errorData: Record<string, unknown>): string {
  const nested = errorData.error;
  if (nested && typeof nested === 'object' && nested !== null && 'message' in nested) {
    return String((nested as { message: unknown }).message);
  }
  const detail = errorData.detail;
  if (typeof detail === 'string') return detail;
  if (detail && typeof detail === 'object' && !Array.isArray(detail) && 'message' in detail) {
    return String((detail as { message: unknown }).message);
  }
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (item && typeof item === 'object' && 'msg' in item) {
          const loc = Array.isArray((item as { loc?: unknown }).loc)
            ? (item as { loc: unknown[] }).loc.join('.')
            : '';
          return loc ? `${loc}: ${(item as { msg: unknown }).msg}` : String((item as { msg: unknown }).msg);
        }
        return String(item);
      })
      .join('; ');
  }
  if (typeof errorData.message === 'string') return errorData.message;
  if (typeof errorData.error === 'string') return errorData.error;
  return 'An error occurred';
}

/** Login 422 with body.username usually means another app's API is on port 8000 (e.g. ServiceBridge). */
export function isForeignAuthApiError(errorData: Record<string, unknown>): boolean {
  const detail = errorData.detail;
  if (!Array.isArray(detail)) return false;
  return detail.some((item) => {
    if (!item || typeof item !== 'object' || !('loc' in item)) return false;
    const loc = (item as { loc?: unknown }).loc;
    return Array.isArray(loc) && loc.some((part) => part === 'username');
  });
}

export const FOREIGN_AUTH_API_MESSAGE =
  'Wrong backend on port 8000 (another project may be running). From the tendoriq folder run: run.bat stop — then run.bat';

export function parseApiErrorCode(errorData: Record<string, unknown>): string | undefined {
  const nested = errorData.error;
  if (nested && typeof nested === 'object' && nested !== null && 'code' in nested) {
    return String((nested as { code: unknown }).code);
  }
  if (typeof errorData.code === 'string') return errorData.code;
  const detail = errorData.detail;
  if (detail && typeof detail === 'object' && !Array.isArray(detail) && 'code' in detail) {
    return String((detail as { code: unknown }).code);
  }
  return undefined;
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
  const envelope = payload as ApiEnvelope<T[]> & {
    page?: number;
    limit?: number;
    total?: number;
  };
  return {
    data: (unwrapData(envelope) ?? []) as T[],
    meta: parsePaginationMeta(envelope.meta, {
      page: envelope.page,
      limit: envelope.limit,
      total: envelope.total,
    }),
  };
}

export {
  mapTenderFromApi,
  mapTenderToApi,
  formatTenderDeadline,
  formatTenderValue,
  type ApiTender,
  type ClientTender,
} from '@/shared/tenders';
