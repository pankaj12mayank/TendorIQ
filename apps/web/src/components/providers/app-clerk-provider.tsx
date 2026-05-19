'use client';

import dynamic from 'next/dynamic';
import type { ReactNode } from 'react';

import { isClerkConfigured } from '@/lib/clerk-config';

const ClerkProvider = dynamic(
  () => import('@clerk/nextjs').then((m) => m.ClerkProvider),
  { ssr: false }
);

export function AppClerkProvider({ children }: { children: ReactNode }) {
  if (!isClerkConfigured()) {
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
