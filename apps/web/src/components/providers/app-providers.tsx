'use client';

import type { ReactNode } from 'react';

import { AppClerkProvider } from '@/components/providers/app-clerk-provider';
import { ThemeProvider } from '@/components/providers/theme-provider';
import { TooltipProvider } from '@/components/ui/tooltip';
import { AuthProvider } from '@/hooks/use-auth';
import { QueryProvider } from '@/lib/query-client';

/**
 * Root client providers only — no class ErrorBoundary here (breaks webpack chunks in dev).
 * Use app/error.tsx for route errors.
 */
export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <AppClerkProvider>
      <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
        <AuthProvider>
          <TooltipProvider>
            <QueryProvider>{children}</QueryProvider>
          </TooltipProvider>
        </AuthProvider>
      </ThemeProvider>
    </AppClerkProvider>
  );
}
