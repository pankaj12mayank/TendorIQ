'use client';

import Link from 'next/link';
import type { ReactNode } from 'react';

import { Button, type ButtonProps } from '@/components/ui/button';
import { useLazyClientModule } from '@/lib/lazy-client-module';
import { isClerkConfigured } from '@/lib/clerk-config';

type Props = {
  children: ReactNode;
  mode?: 'modal' | 'redirect';
  variant?: ButtonProps['variant'];
  className?: string;
};

function LocalSignInButton({ children, variant = 'ghost', className }: Props) {
  return (
    <Button asChild variant={variant} className={className}>
      <Link href="/sign-in">{children}</Link>
    </Button>
  );
}

function LocalSignUpButton({ children, className }: Props) {
  return (
    <Button asChild className={className}>
      <Link href="/sign-up">{children}</Link>
    </Button>
  );
}

export function AuthSignInButton({ variant, className, ...props }: Props) {
  const clerkEnabled = isClerkConfigured();
  const ClerkSignInButton = useLazyClientModule<Props>(
    clerkEnabled,
    () => import('./auth-buttons-clerk'),
    'ClerkSignInButton'
  );

  if (!clerkEnabled || !ClerkSignInButton) {
    return <LocalSignInButton variant={variant} className={className} {...props} />;
  }
  return <ClerkSignInButton variant={variant} className={className} {...props} />;
}

export function AuthSignUpButton({ className, ...props }: Props) {
  const clerkEnabled = isClerkConfigured();
  const ClerkSignUpButton = useLazyClientModule<Props>(
    clerkEnabled,
    () => import('./auth-buttons-clerk'),
    'ClerkSignUpButton'
  );

  if (!clerkEnabled || !ClerkSignUpButton) {
    return <LocalSignUpButton className={className} {...props} />;
  }
  return <ClerkSignUpButton className={className} {...props} />;
}
