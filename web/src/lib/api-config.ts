/** Shared API base URL and timeout defaults for the web app. */

import { API_ROUTE_PREFIX } from '@/shared/constants';

export { API_ROUTE_PREFIX };

export const DEFAULT_API_TIMEOUT_MS = 30_000;
export const UPLOAD_API_TIMEOUT_MS = 120_000;

export function getApiBaseUrl(): string {
  return (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');
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
