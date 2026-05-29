/** Client-side 401 handler — avoids full page reload from api-client when a router is registered. */

export type UnauthorizedInfo = {
  pathname: string;
  search: string;
};

export type UnauthorizedHandler = (info: UnauthorizedInfo) => void;
export type SessionInvalidateHandler = () => void;

let handler: UnauthorizedHandler | null = null;
let sessionInvalidateHandler: SessionInvalidateHandler | null = null;
let lastNotifyAt = 0;

const NOTIFY_DEBOUNCE_MS = 2000;

export function setUnauthorizedHandler(next: UnauthorizedHandler | null): void {
  handler = next;
}

export function setSessionInvalidateHandler(next: SessionInvalidateHandler | null): void {
  sessionInvalidateHandler = next;
}

/** @internal test helper */
export function resetUnauthorizedNotifyStateForTests(): void {
  lastNotifyAt = 0;
}

export function notifyUnauthorized(): void {
  if (typeof window === 'undefined') return;
  const now = Date.now();
  if (now - lastNotifyAt < NOTIFY_DEBOUNCE_MS) return;
  lastNotifyAt = now;

  sessionInvalidateHandler?.();

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
