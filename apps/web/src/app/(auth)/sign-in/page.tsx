'use client';

import Link from 'next/link';

import { SignIn } from '@clerk/nextjs';
import { Button } from '@/components/ui/button';
import { isClerkConfigured } from '@/lib/clerk-config';

export default function SignInPage() {
  if (!isClerkConfigured()) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-6 p-6 text-center">
        <div className="max-w-lg space-y-3">
          <h1 className="text-2xl font-semibold">Tenant sign in</h1>
          <p className="text-muted-foreground">
            Tenant accounts use Clerk. Add your keys to <code>apps/web/.env.local</code>:
          </p>
          <pre className="rounded-lg bg-muted p-4 text-left text-xs">
            {`NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...\nCLERK_SECRET_KEY=sk_test_...`}
          </pre>
          <p className="text-sm text-muted-foreground">
            After sign-in, new organizations complete onboarding, then invite team members by plan.
          </p>
        </div>
        <div className="flex flex-wrap justify-center gap-3">
          <Button asChild variant="ghost">
            <Link href="/forgot-password">Forgot password?</Link>
          </Button>
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
      <SignIn forceRedirectUrl="/onboarding" signUpUrl="/sign-up" />
      <p className="text-sm text-muted-foreground">
        Platform admin?{' '}
        <Link href="/admin/login" className="text-primary hover:underline">
          Super Admin login
        </Link>
      </p>
    </div>
  );
}
