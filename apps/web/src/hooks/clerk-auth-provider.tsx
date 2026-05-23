'use client';

import { useAuth as useClerkAuth, useUser, useSession } from '@clerk/nextjs';
import { useRouter, usePathname } from 'next/navigation';
import { useEffect, useCallback, useMemo, useState, type ReactNode } from 'react';

import {
  clearStoredSession,
  getStoredSession,
  setStoredSession,
  type AuthUser,
} from '@/lib/auth-session';
import {
  exchangeClerkSession,
  tokensFromLoginResponse,
  userFromLoginResponse,
} from '@/lib/auth-api';
import { getPostLoginPath } from '@/lib/auth-redirect';
import { apiUrl as resolveApiUrl } from '@/lib/api-config';
import { buildApiAuthHeaders } from '@/lib/auth-user';
import { parseApiErrorMessage } from '@/lib/api-envelope';
import { isProtectedPath } from '@/lib/clerk-config';
import { isSuperAdmin } from '@/lib/permissions';
import { toast } from 'sonner';

import { AuthContext, type AuthContextValue } from './auth-context';

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

export function ClerkAuthProvider({ children }: { children: ReactNode }) {
  const { isLoaded, isSignedIn, signOut: clerkSignOut } = useClerkAuth();
  const { user: clerkUser } = useUser();
  const { session } = useSession();
  const router = useRouter();
  const pathname = usePathname();
  const [syncedUser, setSyncedUser] = useState<AuthUser | null>(null);
  const [syncing, setSyncing] = useState(false);

  const stored = typeof window !== 'undefined' ? getStoredSession() : null;

  useEffect(() => {
    if (!isLoaded || !isSignedIn || !session) {
      if (!isSignedIn) setSyncedUser(null);
      return;
    }

    let cancelled = false;
    setSyncing(true);

    (async () => {
      try {
        const clerkToken = await session.getToken();
        if (!clerkToken || cancelled) return;

        const exchanged = await exchangeClerkSession(clerkToken);
        if (cancelled) return;

        if (exchanged) {
          setStoredSession(exchanged.token, exchanged.user, {
            refreshToken: exchanged.refreshToken,
            expiresInSec: exchanged.expiresIn,
          });
          setSyncedUser(exchanged.user);
          return;
        }
      } finally {
        if (!cancelled) setSyncing(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [isLoaded, isSignedIn, session, clerkUser?.id]);

  const authUser: AuthUser | null = syncedUser ?? stored?.user ?? null;

  const isAuthenticated = (isLoaded && !!isSignedIn) || !!stored;

  const routeRole =
    authUser?.membershipRole ??
    authUser?.role ??
    (clerkUser?.publicMetadata?.membership_role as string | undefined) ??
    (clerkUser?.publicMetadata?.role as string | undefined);

  useRouteGuard(isAuthenticated, !isLoaded || syncing, routeRole);

  useEffect(() => {
    if (!isLoaded || !isSignedIn || !authUser) return;
    if (isSuperAdmin(authUser.role) && pathname.startsWith('/dashboard') && !pathname.includes('/admin')) {
      router.replace('/dashboard/admin');
    }
  }, [isLoaded, isSignedIn, authUser, pathname, router]);

  const signOut = useCallback(async () => {
    const token = getStoredSession()?.token;
    if (token) {
      try {
        await fetch(resolveApiUrl('/api/v1/auth/logout'), {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...buildApiAuthHeaders(token, authUser ?? undefined),
          },
        });
      } catch {
        // continue
      }
    }
    clearStoredSession();
    setSyncedUser(null);
    await clerkSignOut();
    router.push('/');
  }, [clerkSignOut, router, authUser]);

  const getToken = useCallback(async () => {
    const local = getStoredSession()?.token;
    if (local) return local;
    try {
      return (await session?.getToken()) ?? null;
    } catch {
      return null;
    }
  }, [session]);

  const loginWithCredentials = useCallback(
    async (email: string, password: string) => {
      const res = await fetch(resolveApiUrl('/api/v1/auth/login'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        const err = (await res.json().catch(() => ({}))) as Record<string, unknown>;
        throw new Error(parseApiErrorMessage(err) || 'Login failed');
      }
      const data = await res.json();
      const tokens = tokensFromLoginResponse(data);
      const sessionUser = userFromLoginResponse(data);
      setStoredSession(tokens.access_token, sessionUser, {
        refreshToken: tokens.refresh_token,
        expiresInSec: tokens.expires_in,
      });
      setSyncedUser(sessionUser);
      toast.success('Signed in successfully');
      router.push(
        getPostLoginPath(role === 'super_admin' ? role : membershipRole)
      );
    },
    [router]
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      isAuthenticated,
      isLoading: !isLoaded || syncing,
      user: authUser,
      signOut,
      getToken,
      loginWithCredentials,
    }),
    [isAuthenticated, isLoaded, syncing, authUser, signOut, getToken, loginWithCredentials]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
