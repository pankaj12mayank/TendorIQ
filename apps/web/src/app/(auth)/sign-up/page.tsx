'use client';

import Link from 'next/link';

import { SignUp } from '@clerk/nextjs';
import { Button } from '@/components/ui/button';
import { isClerkConfigured } from '@/lib/clerk-config';

export default function SignUpPage() {
  if (!isClerkConfigured()) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-6 p-6 text-center">
        <div className="max-w-lg space-y-3">
          <h1 className="text-2xl font-semibold">Create tenant account</h1>
          <p className="text-muted-foreground">
            New organizations sign up with Clerk, complete onboarding, then add team members based on
            their subscription plan.
          </p>
          <p className="text-sm text-muted-foreground">
            Configure <code>NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY</code> in{' '}
            <code>apps/web/.env.local</code> to enable tenant registration.
          </p>
        </div>
        <div className="flex flex-wrap justify-center gap-3">
          <Button asChild variant="outline">
            <Link href="/admin/login">Super Admin login</Link>
          </Button>
          <Button asChild>
            <Link href="/">Back to home</Link>
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 p-6">
      <SignUp forceRedirectUrl="/onboarding" signInUrl="/sign-in" />
      <p className="text-sm text-muted-foreground">
        Platform admin?{' '}
        <Link href="/admin/login" className="text-primary hover:underline">
          Super Admin login
        </Link>
      </p>
    </div>
  );
}
