'use client';

import { SignInButton, SignUpButton } from '@clerk/nextjs';
import type { ReactNode } from 'react';

type Props = {
  children: ReactNode;
  mode?: 'modal' | 'redirect';
};

export function ClerkSignInButton(props: Props) {
  return <SignInButton {...props} />;
}

export function ClerkSignUpButton(props: Props) {
  return <SignUpButton {...props} />;
}
