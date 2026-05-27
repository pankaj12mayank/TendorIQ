'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useState, type ComponentType } from 'react';
import { Sparkles } from 'lucide-react';
import { appToast } from '@/lib/app-toast';
import { usePublicBranding } from '@/hooks/use-public-branding';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { PasswordInput } from '@/components/ui/password-input';
import {
  tokensFromLoginResponse,
  userFromLoginResponse,
} from '@/lib/auth-api';
import { apiUrl } from '@/lib/api-config';
import { getPostLoginPath } from '@/lib/auth-redirect';
import { setStoredSession } from '@/lib/auth-session';
import { isClerkConfigured } from '@/lib/clerk-config';
import { getAuthProvider } from '@/lib/auth-provider';

export default function SignUpPage() {
  const router = useRouter();
  const provider = getAuthProvider();
  const isLocalAuth = provider === 'local';
  const clerkEnabled = provider === 'clerk' && isClerkConfigured();
  const [ClerkView, setClerkView] = useState<ComponentType | null>(null);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const branding = usePublicBranding();

  useEffect(() => {
    if (!clerkEnabled) return;
    void import('./sign-up-clerk').then((m) => setClerkView(() => m.default));
  }, [clerkEnabled]);

  async function handleLocalSignUp(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const res = await fetch(apiUrl('/auth/register'), {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, name: name || undefined }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = (body as { detail?: string; error?: { message?: string } }).detail;
        const msg =
          (typeof detail === 'string' ? detail : undefined) ||
          (body as { error?: { message?: string } }).error?.message ||
          'Registration failed';
        throw new Error(msg);
      }
      const tokens = tokensFromLoginResponse(body);
      const authUser = userFromLoginResponse(body);
      setStoredSession(tokens.access_token, authUser, {
        refreshToken: tokens.refresh_token,
        expiresInSec: tokens.expires_in,
      });
      appToast.success('Account created.');
      router.push(
        getPostLoginPath(
          authUser.role === 'super_admin'
            ? authUser.role
            : authUser.membershipRole ?? authUser.role
        )
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setSubmitting(false);
    }
  }

  if (isLocalAuth) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-background to-muted/30 p-6">
        <div className="w-full max-w-md space-y-6 rounded-2xl border bg-card p-8 shadow-lg">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
              <Sparkles className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h1 className="text-xl font-semibold">
                Create your {branding.brand_name || 'TenderIQ'} account
              </h1>
              <p className="text-sm text-muted-foreground">
                {branding.auth_tagline ||
                  'Register with email and password. Your account is stored securely in the database.'}
              </p>
            </div>
          </div>
          <form onSubmit={handleLocalSignUp} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                autoComplete="name"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <PasswordInput
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="new-password"
                required
                minLength={8}
              />
              <p className="text-xs text-muted-foreground">At least 8 characters</p>
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button type="submit" className="w-full" disabled={submitting}>
              {submitting ? 'Creating account...' : 'Create account'}
            </Button>
          </form>
          <p className="text-center text-sm text-muted-foreground">
            Already have an account?{' '}
            <Link href="/sign-in" className="text-primary hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    );
  }

  if (clerkEnabled && ClerkView) {
    return <ClerkView />;
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 p-6 text-center">
      <p className="text-muted-foreground">Authentication is not configured.</p>
      <Button asChild variant="outline">
        <Link href="/">Home</Link>
      </Button>
    </div>
  );
}
