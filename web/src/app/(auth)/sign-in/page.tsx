'use client';

import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { useState } from 'react';
import { Shield } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { PasswordInput } from '@/components/ui/password-input';
import { Label } from '@/components/ui/label';
import { useAuthContext } from '@/hooks/use-auth';
import { isClerkConfigured } from '@/lib/clerk-config';
import { useLazyClientModule } from '@/lib/lazy-client-module';
import { getAuthProvider } from '@/lib/supabase-config';

export default function SignInPage() {
  const searchParams = useSearchParams();
  const orgSlug = (searchParams.get('org') ?? '').trim().toLowerCase();
  const { loginWithCredentials, isAuthenticated, isLoading, user } = useAuthContext();
  const clerkEnabled = isClerkConfigured();
  const ClerkView = useLazyClientModule(
    clerkEnabled,
    () => import('./sign-in-clerk')
  );
  const isLocalAuth = getAuthProvider() === 'local';
  const [email, setEmail] = useState(isLocalAuth ? 'demo@tendoriq.com' : '');
  const [password, setPassword] = useState(isLocalAuth ? 'Demo@123' : '');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await loginWithCredentials(email, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setSubmitting(false);
    }
  }

  if (!isLoading && isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center p-6">
        <p className="text-muted-foreground">Signed in as {user?.email}. Redirecting...</p>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-background to-muted/30 p-6">
      <div className="w-full max-w-md space-y-6 rounded-2xl border bg-card p-8 shadow-lg">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
            <Shield className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-xl font-semibold">Sign in to TenderIQ</h1>
            <p className="text-sm text-muted-foreground">
              One login for all roles — access is based on your account role.
            </p>
          </div>
        </div>

        {isLocalAuth && (
          <div className="rounded-lg border border-dashed bg-muted/40 p-3 text-sm">
            <p className="font-medium text-foreground">Local dev — no cloud keys</p>
            <p className="mt-1 text-muted-foreground">
              Demo: <code className="text-xs">demo@tendoriq.com</code> / <code className="text-xs">Demo@123</code>
              <br />
              Admin: <code className="text-xs">admin@tenderiq.com</code> /{' '}
              <code className="text-xs">SuperAdmin@123</code>
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => {
                  setEmail('demo@tendoriq.com');
                  setPassword('Demo@123');
                }}
              >
                Fill demo
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => {
                  setEmail('admin@tendoriq.com');
                  setPassword('SuperAdmin@123');
                }}
              >
                Fill admin
              </Button>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="password">Password</Label>
              <Link
                href="/forgot-password"
                className="text-xs text-primary hover:underline"
              >
                Forgot password?
              </Link>
            </div>
            <PasswordInput
              id="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
          <Button type="submit" className="w-full" disabled={submitting}>
            {submitting ? 'Signing in...' : 'Sign in'}
          </Button>
        </form>

        {clerkEnabled && ClerkView && (
          <>
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-card px-2 text-muted-foreground">Or continue with SSO</span>
              </div>
            </div>
            <ClerkView />
          </>
        )}

        <p className="text-center text-sm text-muted-foreground">
          <Link href="/" className="text-primary hover:underline">
            Home
          </Link>
        </p>
      </div>
    </div>
  );
}
