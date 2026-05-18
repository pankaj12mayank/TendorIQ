'use client';

import { useAuth, useUser, useSession } from '@clerk/nextjs';
import { useRouter, usePathname } from 'next/navigation';
import { useEffect, useCallback, createContext, useContext, type ReactNode } from 'react';

export interface AuthUser {
  id: string;
  email: string;
  name: string;
  imageUrl?: string;
  role?: string;
}

export interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: AuthUser | null;
}

interface AuthContextValue extends AuthState {
  signOut: () => Promise<void>;
  getToken: () => Promise<string | null>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const { isLoaded, isSignedIn, signOut: clerkSignOut } = useAuth();
  const { user } = useUser();
  const { getToken } = useSession();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (isLoaded && !isSignedIn) {
      const signInUrl = new URL('/sign-in', window.location.origin);
      signInUrl.searchParams.set('redirect_url', pathname);
      router.push(signInUrl.toString());
    }
  }, [isLoaded, isSignedIn, router, pathname]);

  const handleSignOut = useCallback(async () => {
    await clerkSignOut();
    router.push('/sign-in');
  }, [clerkSignOut, router]);

  const handleGetToken = useCallback(async () => {
    try {
      return await getToken();
    } catch {
      return null;
    }
  }, [getToken]);

  const value: AuthContextValue = {
    isAuthenticated: isLoaded && isSignedIn,
    isLoading: !isLoaded,
    user: user
      ? {
          id: user.id,
          email: user.emailAddresses[0]?.emailAddress || '',
          name: user.fullName || user.username || '',
          imageUrl: user.imageUrl,
          role: user.publicMetadata?.role as string | undefined,
        }
      : null,
    signOut: handleSignOut,
    getToken: handleGetToken,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuthContext() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuthContext must be used within AuthProvider');
  }
  return context;
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