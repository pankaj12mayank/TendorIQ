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
import { toast } from 'sonner';

import {
  clearStoredSession,
  getStoredSession,
  getSessionTimeRemainingMs,
  setStoredSession,
  SESSION_MAX_AGE_MS,
  type AuthUser,
} from '@/lib/auth-session';
import { getPostLoginPath } from '@/lib/auth-redirect';
import { isClerkConfigured, isProtectedPath } from '@/lib/clerk-config';
import { getRolePermissions } from '@/lib/permissions';
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

async function fetchMe(token: string): Promise<AuthUser | null> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  try {
    const res = await fetch(`${apiUrl}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return null;
    const data = await res.json();
    return {
      id: data.user_id ?? data.email,
      email: data.email,
      name: data.email?.split('@')[0] ?? 'User',
      role: data.role,
      permissions: data.permissions,
    };
  } catch {
    return null;
  }
}

function LocalAuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

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

      const me = await fetchMe(session.token);
      const restored: AuthUser = me
        ? { ...me, name: me.name || session.user.name }
        : {
            ...session.user,
            permissions: getRolePermissions(session.user.role),
          };

      if (!cancelled) {
        setUser(restored);
        setStoredSession(session.token, restored);
        setIsLoading(false);
      }

      const remaining = getSessionTimeRemainingMs();
      if (remaining > 0 && remaining < 15 * 60 * 1000) {
        toast.info('Your session will expire soon. Please save your work.');
      }
    }

    void restore();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      const session = getStoredSession();
      if (!session) {
        setUser(null);
        toast.error('Your session has expired. Please sign in again.');
        router.replace('/sign-in');
      }
    }, 60_000);
    return () => clearInterval(interval);
  }, [router]);

  useRouteGuard(!!user, isLoading, user?.role);

  const signOut = useCallback(async () => {
    clearStoredSession();
    setUser(null);
    router.push('/');
  }, [router]);

  const getToken = useCallback(async () => getStoredSession()?.token ?? null, []);

  const loginWithCredentials = useCallback(
    async (email: string, password: string) => {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiUrl}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error((err as { detail?: string }).detail || 'Login failed');
      }
      const data = await res.json();
      const role = (data.user?.role as string) || 'user';
      const authUser: AuthUser = {
        id: data.user?.email ?? email,
        email: data.user?.email ?? email,
        name: data.user?.name ?? email.split('@')[0] ?? 'User',
        role,
        permissions: getRolePermissions(role),
      };
      setStoredSession(data.token, authUser);
      setUser(authUser);
      toast.success('Signed in successfully');
      const params = new URLSearchParams(window.location.search);
      const redirectUrl = params.get('redirect_url');
      if (redirectUrl && redirectUrl.startsWith('/dashboard')) {
        router.push(redirectUrl);
      } else {
        router.push(getPostLoginPath(role));
      }
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
  const clerkEnabled = isClerkConfigured();
  const ClerkAuthProvider = useLazyClientModule<{ children: ReactNode }>(
    clerkEnabled,
    () => import('./clerk-auth-provider'),
    'ClerkAuthProvider'
  );

  if (clerkEnabled && ClerkAuthProvider) {
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
