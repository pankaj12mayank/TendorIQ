'use client';

import { SignIn } from '@clerk/nextjs';

/** Clerk SSO block on the unified sign-in page (no separate tenant login). */
export default function SignInClerk() {
  return (
    <SignIn forceRedirectUrl="/onboarding" signUpUrl="/sign-up" routing="hash" />
  );
}
