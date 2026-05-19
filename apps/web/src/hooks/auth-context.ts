'use client';

import { createContext } from 'react';

import type { AuthUser } from '@/lib/auth-session';

export interface AuthContextValue {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: AuthUser | null;
  signOut: () => Promise<void>;
  getToken: () => Promise<string | null>;
  loginWithSuperAdmin: (email: string, password: string) => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | null>(null);
