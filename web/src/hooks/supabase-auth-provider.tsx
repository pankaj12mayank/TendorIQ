'use client';

import { useRouter, usePathname } from 'next/navigation';
import {
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { toast } from 'sonner';

import {
  clearStoredSession,
  getStoredSession,
  setStoredSession,
  SESSION_MAX_AGE_MS,
  type AuthUser,
} from '@/lib/auth-session';
import {
  exchangeSupabaseSession,
  fetchMeFromApi,
  refreshAccessToken,
} from '@/lib/auth-api';
import { getPostLoginPath } from '@/lib/auth-redirect';
import { setUnauthorizedHandler } from '@/lib/auth-unauthorized';
import { isProtectedPath } from '@/lib/clerk-config';
import { getSupabaseBrowserClient } from '@/lib/supabase/client';

import { AuthContext, type AuthContextValue } from './auth-context';

function useRouteGuard(isAuthenticated: boolean, isLoading: boolean, role?: string) {
  const router = useRouter();
  const pathname = usePathname();
  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated && isProtectedPath(pathname)) {
      const url = new URL('/sign-in', window.location.origin);
      url.searchParams.set('redirect_url', pathname + window.location.search);
      router.replace(url.toString());
      return;
    }
    if (isAuthenticated && (pathname === '/sign-in' || pathname === '/sign-up')) {
      router.replace(getPostLoginPath(role));
    }
  }, [isAuthenticated, isLoading, pathname, router, role]);
}

export function SupabaseAuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const supabase = getSupabaseBrowserClient();

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

  const syncFromSupabase = useCallback(async () => {
    if (!supabase) {
      setIsLoading(false);
      return;
    }
    const { data } = await supabase.auth.getSession();
    const accessToken = data.session?.access_token;
    if (!accessToken) {
      const stored = getStoredSession();
      if (stored?.token) {
        const me = await fetchMeFromApi(stored.token, stored.user);
        if (me.user) {
          setUser(me.user);
          setIsLoading(false);
          return;
        }
        clearStoredSession();
      }
      setUser(null);
      setIsLoading(false);
      return;
    }

    const exchanged = await exchangeSupabaseSession(accessToken);
    if (!exchanged) {
      setUser(null);
      setIsLoading(false);
      return;
    }
    setStoredSession(exchanged.token, exchanged.user, {
      refreshToken: exchanged.refreshToken,
      expiresInSec: exchanged.expiresIn,
    });
    setUser(exchanged.user);
    setIsLoading(false);
  }, [supabase]);

  useEffect(() => {
    void syncFromSupabase();
    if (!supabase) return;
    const { data: sub } = supabase.auth.onAuthStateChange(() => {
      void syncFromSupabase();
    });
    return () => sub.subscription.unsubscribe();
  }, [supabase, syncFromSupabase]);

  useRouteGuard(!!user, isLoading, user?.role);

  const signOut = useCallback(async () => {
    if (supabase) await supabase.auth.signOut();
    clearStoredSession();
    setUser(null);
    router.replace('/sign-in');
  }, [supabase, router]);

  const getToken = useCallback(async () => {
    const stored = getStoredSession();
    if (!stored?.token) return null;
    if (stored.refreshToken && stored.expiresAt && Date.now() > stored.expiresAt - 60_000) {
      const refreshed = await refreshAccessToken(stored.refreshToken);
      if (refreshed?.access_token) {
        setStoredSession(refreshed.access_token, stored.user, {
          refreshToken: refreshed.refresh_token,
          expiresInSec: refreshed.expires_in,
        });
        return refreshed.access_token;
      }
    }
    return stored.token;
  }, []);

  const loginWithCredentials = useCallback(
    async (email: string, password: string) => {
      if (!supabase) throw new Error('Supabase is not configured');
      const { data, error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) throw new Error(error.message);
      const token = data.session?.access_token;
      if (!token) throw new Error('No session returned');
      const exchanged = await exchangeSupabaseSession(token);
      if (!exchanged) throw new Error('Failed to exchange session with API');
      setStoredSession(exchanged.token, exchanged.user, {
        refreshToken: exchanged.refreshToken,
        expiresInSec: exchanged.expiresIn,
      });
      setUser(exchanged.user);
      toast.success('Signed in successfully');
      router.push(getPostLoginPath(exchanged.user.membershipRole ?? exchanged.user.role));
    },
    [supabase, router]
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
