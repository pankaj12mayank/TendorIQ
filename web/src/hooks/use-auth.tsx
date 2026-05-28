'use client';

import { useRouter, usePathname } from 'next/navigation';
import {
  useEffect,
  useCallback,
  useContext,
  useState,
  useMemo,
  type ReactNode,
} from 'react';
import { appToast } from '@/lib/app-toast';

import {
  clearStoredSession,
  getStoredSession,
  getSessionLastActivityMs,
  getSessionTimeRemainingMs,
  markSessionActivity,
  setStoredSession,
  SESSION_MAX_AGE_MS,
  type AuthUser,
} from '@/lib/auth-session';
import { apiUrl } from '@/lib/api-config';
import {
  fetchMeFromApi,
  refreshAccessToken,
  tokensFromLoginResponse,
  userFromLoginResponse,
} from '@/lib/auth-api';
import { getPostLoginPath } from '@/lib/auth-redirect';
import { buildApiAuthHeaders } from '@/lib/auth-user';
import { syncTenantStoreFromUser } from '@/lib/sync-tenant-store';
import { parseApiErrorMessage } from '@/lib/api-envelope';
import { setUnauthorizedHandler } from '@/lib/auth-unauthorized';
import { isClerkConfigured, isProtectedPath } from '@/lib/clerk-config';
import { getAuthProvider } from '@/lib/auth-provider';
import { useLazyClientModule } from '@/lib/lazy-client-module';

import { AuthContext, type AuthContextValue } from './auth-context';

export type { AuthUser, AuthContextValue };

function useRouteGuard(isAuthenticated: boolean, isLoading: boolean, role?: string) {
  const router = useRouter();
  const pathname = usePathname();
  useEffect(() => {
    if (isLoading) return;

    if (!isAuthenticated && isProtectedPath(pathname)) {
      const url = new URL('/sign-in', window.location.origin);
      const redirect = pathname + window.location.search;
      url.searchParams.set('redirect_url', redirect);
      router.replace(url.toString());
      return;
    }

    if (isAuthenticated && (pathname === '/sign-in' || pathname === '/sign-up')) {
      const params = new URLSearchParams(window.location.search);
      const redirectUrl = params.get('redirect_url');
      if (redirectUrl && redirectUrl.startsWith('/dashboard')) {
        router.replace(redirectUrl);
      } else {
        router.replace(getPostLoginPath(role));
      }
    }
  }, [isAuthenticated, isLoading, pathname, router, role]);
}

function LocalAuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    setUnauthorizedHandler(({ pathname, search }) => {
      const url = new URL('/sign-in', window.location.origin);
      if (pathname.startsWith('/dashboard') || pathname.startsWith('/admin')) {
        url.searchParams.set('redirect_url', pathname + search);
      }
      router.replace(url.pathname + url.search);
    });
    return () => setUnauthorizedHandler(null);
  }, [router]);

  useEffect(() => {
    let cancelled = false;

    async function restore() {
      const session = getStoredSession();
      if (!session) {
        if (!cancelled) {
          setUser(null);
          setIsLoading(false);
        }
        return;
      }

      let accessToken = session.token;
      let refreshToken = session.refreshToken;

      let { user: me, unauthorized, networkError } = await fetchMeFromApi(
        accessToken,
        session.user
      );

      if (networkError) {
        if (!cancelled) {
          setUser(session.user);
          setIsLoading(false);
          appToast.error('API is not reachable. Run run.bat and keep the API window open.');
        }
        return;
      }

      if (unauthorized && refreshToken) {
        const refreshed = await refreshAccessToken(refreshToken);
        if (refreshed) {
          accessToken = refreshed.access_token;
          refreshToken = refreshed.refresh_token ?? refreshToken;
          const retry = await fetchMeFromApi(accessToken, session.user);
          me = retry.user;
          unauthorized = retry.unauthorized;
          if (retry.networkError) {
            if (!cancelled) {
              setUser(session.user);
              setIsLoading(false);
              appToast.error('API is not reachable. Run run.bat and keep the API window open.');
            }
            return;
          }
        }
      }

      if (unauthorized) {
        clearStoredSession();
        if (!cancelled) {
          setUser(null);
          setIsLoading(false);
        }
        return;
      }

      const restored: AuthUser = me
        ? {
            ...me,
            name: me.name || session.user.name,
            permissions: me.permissions?.length ? me.permissions : session.user.permissions,
            membershipRole: me.membershipRole ?? session.user.membershipRole,
            tenantId: me.tenantId ?? session.user.tenantId,
          }
        : session.user;

      if (!cancelled) {
        setUser(restored);
        setStoredSession(accessToken, restored, {
          refreshToken,
        });
        markSessionActivity();
        setIsLoading(false);
      }

      const remaining = getSessionTimeRemainingMs();
      if (remaining > 0 && remaining < 15 * 60 * 1000) {
        appToast.info('Your session will expire soon. Please save your work.');
      }
    }

    void restore();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let notified = false;
    const inactivityLimit = SESSION_MAX_AGE_MS;
    const interval = setInterval(() => {
      const session = getStoredSession();
      if (!session && !notified) {
        notified = true;
        setUser(null);
        appToast.error('Your session has expired. Please sign in again.');
        router.replace('/sign-in');
        return;
      }
      const lastActive = getSessionLastActivityMs();
      if (session && lastActive && Date.now() - lastActive > inactivityLimit) {
        clearStoredSession();
        setUser(null);
        appToast.error('Logged out due to inactivity.');
        router.replace('/sign-in');
      }
    }, 60_000);
    return () => clearInterval(interval);
  }, [router]);

  useEffect(() => {
    if (!user) return;
    const touch = () => markSessionActivity();
    const events: (keyof WindowEventMap)[] = ['click', 'keydown', 'mousemove', 'focus', 'scroll'];
    events.forEach((e) => window.addEventListener(e, touch, { passive: true }));
    touch();
    return () => {
      events.forEach((e) => window.removeEventListener(e, touch));
    };
  }, [user, pathname]);

  useEffect(() => {
    const onStorage = (event: StorageEvent) => {
      if (!event.key || !event.key.startsWith('tenderiq_auth_')) return;
      const session = getStoredSession();
      if (!session) {
        setUser(null);
      }
    };
    window.addEventListener('storage', onStorage);
    return () => window.removeEventListener('storage', onStorage);
  }, []);

  useRouteGuard(!!user, isLoading, user?.role);

  useEffect(() => {
    syncTenantStoreFromUser(user);
  }, [user]);

  const signOut = useCallback(async () => {
    const token = getStoredSession()?.token;
    if (token) {
      try {
        await fetch(apiUrl('/auth/logout'), {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
            ...buildApiAuthHeaders(token, user ?? undefined),
          },
        });
      } catch {
        // Clear local session even if revoke call fails
      }
    }
    clearStoredSession();
    setUser(null);
    router.push('/');
  }, [router, user]);

  const getToken = useCallback(async () => getStoredSession()?.token ?? null, []);

  const loginWithCredentials = useCallback(
    async (email: string, password: string) => {
      let res: Response;
      try {
        res = await fetch(apiUrl('/auth/login'), {
          method: 'POST',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password }),
          signal: AbortSignal.timeout(30_000),
        });
      } catch {
        throw new Error(
          'Cannot reach API at http://localhost:8000. Run run.bat from the tendoriq folder and wait until API is ready.'
        );
      }
      if (!res.ok) {
        const err = (await res.json().catch(() => ({}))) as Record<string, unknown>;
        let message = parseApiErrorMessage(err) || 'Login failed';
        if (res.status === 503 || res.status === 502) {
          message = 'API is not running. Start with run.bat, then try again.';
        }
        throw new Error(message);
      }
      const data = await res.json();
      const tokens = tokensFromLoginResponse(data);
      const authUser = userFromLoginResponse(data);
      setStoredSession(tokens.access_token, authUser, {
        refreshToken: tokens.refresh_token,
        expiresInSec: tokens.expires_in,
      });
      setUser(authUser);
      appToast.success('Signed in successfully.');
      const params = new URLSearchParams(window.location.search);
      const redirectUrl = params.get('redirect_url');

      if (redirectUrl && redirectUrl.startsWith('/dashboard')) {
        router.push(redirectUrl);
        return;
      }

      const postLoginPath = getPostLoginPath(
        authUser.role === 'super_admin'
          ? authUser.role
          : authUser.membershipRole ?? authUser.role
      );
      router.push(postLoginPath);
    },
    [router]
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      isAuthenticated: !!user,
      isLoading,
      user,
      signOut,
      getToken,
      loginWithCredentials,
    }),
    [user, isLoading, signOut, getToken, loginWithCredentials]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const provider = getAuthProvider();
  const ClerkAuthProvider = useLazyClientModule<{ children: ReactNode }>(
    provider === 'clerk' && isClerkConfigured(),
    () => import('./clerk-auth-provider'),
    'ClerkAuthProvider'
  );

  if (provider === 'clerk' && ClerkAuthProvider) {
    return <ClerkAuthProvider>{children}</ClerkAuthProvider>;
  }
  return <LocalAuthProvider>{children}</LocalAuthProvider>;
}

export function useAuthContext() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuthContext must be used within AuthProvider');
  }
  return context;
}

export function useAuth() {
  const { isAuthenticated, isLoading, user } = useAuthContext();
  return {
    isLoaded: !isLoading,
    isSignedIn: isAuthenticated,
    userId: user?.id ?? null,
  };
}

export function useAuthState() {
  const { isAuthenticated, isLoading, user } = useAuthContext();
  return { isAuthenticated, isLoading, user };
}

export function useCurrentUser() {
  const { user } = useAuthContext();
  return user;
}

export function useSignOut() {
  const { signOut } = useAuthContext();
  return signOut;
}

export function useGetToken() {
  const { getToken } = useAuthContext();
  return getToken;
}

export function useLogin() {
  const { loginWithCredentials } = useAuthContext();
  return loginWithCredentials;
}

export { SESSION_MAX_AGE_MS };
