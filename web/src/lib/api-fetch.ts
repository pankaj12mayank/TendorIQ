import { parseApiErrorMessage } from './api-envelope';
import { apiUrl, DEFAULT_API_TIMEOUT_MS } from './api-config';
import { getSessionRequestHeaders } from './api-headers';

export class ApiFetchError extends Error {
  constructor(
    public status: number,
    message: string,
    public code?: string
  ) {
    super(message);
    this.name = 'ApiFetchError';
  }
}

export interface AuthenticatedFetchOptions extends RequestInit {
  /** Request timeout in ms (default {@link DEFAULT_API_TIMEOUT_MS}). */
  timeout?: number;
  /** When false, do not attach session auth headers (public routes). */
  auth?: boolean;
}

/**
 * Low-level fetch to the TenderIQ API with base URL, optional auth headers, and timeout.
 * Use for blob downloads, multipart uploads, and other non-JSON flows.
 */
export async function authenticatedFetch(
  path: string,
  init: AuthenticatedFetchOptions = {}
): Promise<Response> {
  const { timeout = DEFAULT_API_TIMEOUT_MS, auth = true, headers, ...rest } = init;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(apiUrl(path), {
      ...rest,
      credentials: 'include',
      signal: rest.signal ?? controller.signal,
      headers: {
        ...(auth ? (getSessionRequestHeaders() as Record<string, string>) : {}),
        ...(headers as Record<string, string> | undefined),
      },
    });
    return response;
  } finally {
    clearTimeout(timeoutId);
  }
}

export async function authenticatedJson<T>(
  path: string,
  init: AuthenticatedFetchOptions = {}
): Promise<T> {
  const response = await authenticatedFetch(path, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init.headers as Record<string, string> | undefined),
    },
  });

  if (!response.ok) {
    let body: Record<string, unknown> = {};
    try {
      body = (await response.json()) as Record<string, unknown>;
    } catch {
      body = { message: response.statusText };
    }
    throw new ApiFetchError(response.status, parseApiErrorMessage(body));
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
