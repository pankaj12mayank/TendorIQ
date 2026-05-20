'use client';

import type { ReactNode } from 'react';

import { useLazyClientModule } from '@/lib/lazy-client-module';
import { isClerkConfigured } from '@/lib/clerk-config';

export function AppClerkProvider({ children }: { children: ReactNode }) {
  const clerkEnabled = isClerkConfigured();
  const ClerkProvider = useLazyClientModule<{ children: ReactNode; appearance?: object }>(
    clerkEnabled,
    () => import('@clerk/nextjs'),
    'ClerkProvider'
  );

  if (!clerkEnabled || !ClerkProvider) {
    return <>{children}</>;
  }

  return (
    <ClerkProvider
      appearance={{
        elements: {
          formButtonPrimary: 'bg-primary hover:bg-primary/90',
        },
      }}
    >
      {children}
    </ClerkProvider>
  );
}
