'use client';

import Link from 'next/link';
import { SignUp } from '@clerk/nextjs';

export default function SignUpClerk() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 p-6">
      <SignUp forceRedirectUrl="/onboarding" signInUrl="/sign-in" />
      <p className="text-sm text-muted-foreground">
        Already have an account?{' '}
        <Link href="/sign-in" className="text-primary hover:underline">
          Sign in
        </Link>
      </p>
    </div>
  );
}
