'use client';

import Link from 'next/link';
import { useEffect, useState, type ComponentType } from 'react';
import { Sparkles } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { isClerkConfigured } from '@/lib/clerk-config';

export default function SignUpPage() {
  const clerkEnabled = isClerkConfigured();
  const [ClerkView, setClerkView] = useState<ComponentType | null>(null);

  useEffect(() => {
    if (!clerkEnabled) return;
    void import('./sign-up-clerk').then((m) => setClerkView(() => m.default));
  }, [clerkEnabled]);

  if (!clerkEnabled) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-6 p-6 text-center">
        <div className="mx-auto max-w-lg space-y-4">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10">
            <Sparkles className="h-7 w-7 text-primary" />
          </div>
          <h1 className="text-2xl font-semibold">Get started with TenderIQ</h1>
          <p className="text-muted-foreground">
            Create your organization in minutes. Sign in with your work email, complete onboarding,
            and invite your team — no API keys or separate admin logins required.
          </p>
          <p className="text-sm text-muted-foreground">
            Self-serve signup requires Clerk (`NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`). Without Clerk,
            sign in with your demo or workspace credentials, then complete onboarding to create your
            organization.
          </p>
        </div>
        <div className="flex flex-wrap justify-center gap-3">
          <Button asChild className="bg-primary hover:bg-primary/90">
            <Link href="/sign-in">Continue to sign in</Link>
          </Button>
          <Button asChild variant="outline">
            <Link href="/">Back to home</Link>
          </Button>
        </div>
      </div>
    );
  }

  if (!ClerkView) {
    return (
      <div className="flex min-h-screen items-center justify-center text-muted-foreground">
        Loading...
      </div>
    );
  }

  return <ClerkView />;
}
