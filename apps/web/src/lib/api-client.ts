import type { ZodSchema } from 'zod';

import { clearStoredSession, getAuthToken } from '@/lib/auth-session';
import { getSessionRequestHeaders } from '@/lib/api-headers';

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public code?: string,
    public details?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean>;
  schema?: ZodSchema;
  timeout?: number;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  getAuthHeaders(): HeadersInit {
    if (typeof window === 'undefined') return {};
    const sessionHeaders = getSessionRequestHeaders();
    if (Object.keys(sessionHeaders).length > 0) {
      return sessionHeaders;
    }
    const token = getAuthToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  private buildUrl(endpoint: string, params?: Record<string, string | number | boolean>): string {
    const url = new URL(`${this.baseUrl}${endpoint}`);
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        url.searchParams.append(key, String(value));
      });
    }
    return url.toString();
  }

  async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { params, schema, timeout = 30000, ...fetchOptions } = options;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(this.buildUrl(endpoint, params), {
        ...fetchOptions,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...this.getAuthHeaders(),
          ...fetchOptions.headers,
        },
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        if (response.status === 401 && typeof window !== 'undefined') {
          clearStoredSession();
          const path = window.location.pathname + window.location.search;
          if (path.startsWith('/dashboard')) {
            window.location.href = `/sign-in?redirect_url=${encodeURIComponent(path)}`;
          } else if (path.startsWith('/admin')) {
            window.location.href = `/sign-in?redirect_url=${encodeURIComponent(path)}`;
          }
        }

        let errorData: Record<string, unknown> = {};
        try {
          errorData = await response.json();
        } catch {
          errorData = { message: response.statusText };
        }

        const message =
          (errorData.detail as string) ||
          (errorData.error as string) ||
          (errorData.message as string) ||
          'An error occurred';

        throw new ApiError(
          response.status,
          typeof message === 'object' ? JSON.stringify(message) : String(message),
          (errorData.code as string) || 'UNKNOWN_ERROR',
          errorData.details as Record<string, unknown> | undefined
        );
      }

      if (response.status === 204) {
        return undefined as T;
      }

      const data = await response.json();

      if (schema) {
        return schema.parse(data) as T;
      }

      return data as T;
    } catch (err) {
      clearTimeout(timeoutId);
      if (err instanceof DOMException && err.name === 'AbortError') {
        throw new ApiError(408, 'Request timed out', 'TIMEOUT');
      }
      throw err;
    }
  }

  get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  }

  post<T>(endpoint: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'POST', body: JSON.stringify(body) });
  }

  put<T>(endpoint: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'PUT', body: JSON.stringify(body) });
  }

  patch<T>(endpoint: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'PATCH', body: JSON.stringify(body) });
  }

  delete<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  }
}

export const api = new ApiClient();