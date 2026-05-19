'use client';

import dynamic from 'next/dynamic';
import Link from 'next/link';
import type { ReactNode } from 'react';

import { Button, type ButtonProps } from '@/components/ui/button';
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

const ClerkSignInButton = dynamic(
  () => import('./auth-buttons-clerk').then((m) => m.ClerkSignInButton),
  { ssr: false }
);

const ClerkSignUpButton = dynamic(
  () => import('./auth-buttons-clerk').then((m) => m.ClerkSignUpButton),
  { ssr: false }
);

export function AuthSignInButton({ variant, className, ...props }: Props) {
  if (!isClerkConfigured()) {
    return <LocalSignInButton variant={variant} className={className} {...props} />;
  }
  return <ClerkSignInButton {...props} />;
}

export function AuthSignUpButton({ className, ...props }: Props) {
  if (!isClerkConfigured()) {
    return <LocalSignUpButton className={className} {...props} />;
  }
  return <ClerkSignUpButton {...props} />;
}
