/** Shared API base URL and timeout defaults for the web app. */

import { API_ROUTE_PREFIX } from '@/shared/constants';

export { API_ROUTE_PREFIX };

export const DEFAULT_API_TIMEOUT_MS = 30_000;
export const UPLOAD_API_TIMEOUT_MS = 120_000;

/**
 * Browser dev: same-origin `/api/v1` via Next rewrite (no CORS).
 * Server/SSR: direct API URL from env.
 */
export function getApiBaseUrl(): string {
  const configured = (process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000').replace(
    /\/$/,
    ''
  );
  if (typeof window !== 'undefined') {
    const useProxy =
      process.env.NEXT_PUBLIC_USE_API_PROXY !== '0' &&
      (process.env.NODE_ENV === 'development' ||
        process.env.NEXT_PUBLIC_USE_API_PROXY === '1');
    if (useProxy) {
      return '';
    }
  }
  return configured;
}

/** Build an absolute API URL from a path (with or without `/api/v1` prefix). */
export function apiUrl(path: string): string {
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }
  const normalized = path.startsWith('/') ? path : `/${path}`;
  if (normalized.startsWith(API_ROUTE_PREFIX)) {
    return `${getApiBaseUrl()}${normalized}`;
  }
  return `${getApiBaseUrl()}${API_ROUTE_PREFIX}${normalized}`;
}
