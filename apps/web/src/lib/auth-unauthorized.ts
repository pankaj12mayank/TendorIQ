/** Client-side 401 handler — avoids full page reload from api-client when a router is registered. */

export type UnauthorizedInfo = {
  pathname: string;
  search: string;
};

export type UnauthorizedHandler = (info: UnauthorizedInfo) => void;

let handler: UnauthorizedHandler | null = null;

export function setUnauthorizedHandler(next: UnauthorizedHandler | null): void {
  handler = next;
}

export function notifyUnauthorized(): void {
  if (typeof window === 'undefined') return;
  const info = {
    pathname: window.location.pathname,
    search: window.location.search,
  };
  if (handler) {
    handler(info);
    return;
  }
  const path = info.pathname + info.search;
  if (path.startsWith('/dashboard') || path.startsWith('/admin')) {
    window.location.href = `/sign-in?redirect_url=${encodeURIComponent(path)}`;
  }
}
