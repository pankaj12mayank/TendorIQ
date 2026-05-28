'use client';

import Link from 'next/link';
import { useState } from 'react';
import { FileSearch, Shield, Sparkles, Upload } from 'lucide-react';

import { CinematicBackground } from '@/components/cinematic/cinematic-background';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { PasswordInput } from '@/components/ui/password-input';
import { Label } from '@/components/ui/label';
import { useAuthContext } from '@/hooks/use-auth';
import { usePublicBranding } from '@/hooks/use-public-branding';
import { isClerkConfigured } from '@/lib/clerk-config';
import { useLazyClientModule } from '@/lib/lazy-client-module';

export default function SignInPage() {
  const { loginWithCredentials, isAuthenticated, isLoading, user } = useAuthContext();
  const clerkEnabled = isClerkConfigured();
  const ClerkView = useLazyClientModule(clerkEnabled, () => import('./sign-in-clerk'));
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const branding = usePublicBranding();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const normalizedEmail = email.trim().toLowerCase();
    if (!normalizedEmail) {
      setError('Email is required');
      return;
    }
    if (!password || password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      await loginWithCredentials(normalizedEmail, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setSubmitting(false);
    }
  }

  if (!isLoading && isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <p className="text-muted-foreground">Signed in as {user?.email}. Redirecting…</p>
      </div>
    );
  }

  return (
    <div className="dark relative min-h-screen bg-background">
      <CinematicBackground intensity="medium" className="fixed inset-0" />
      <div className="auth-shell relative z-10">
        <div className="auth-brand-panel">
          <div className="relative z-10 space-y-8">
            <Link
              href="/"
              className="inline-flex h-12 w-12 items-center justify-center overflow-hidden rounded-2xl bg-white/15 ring-1 ring-white/25"
              aria-label="Go to landing page"
            >
              {branding.logo_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={branding.logo_url} alt="Brand logo" className="h-12 w-12 object-cover" />
              ) : (
                <Shield className="h-6 w-6" />
              )}
            </Link>
            <div>
              <h1 className="font-display text-3xl font-semibold tracking-tight">
                {branding.brand_name || 'TenderIQ'}
              </h1>
              <p className="mt-3 max-w-sm text-sm leading-relaxed text-white/80">
                {branding.hero_subheadline ||
                  'Cinematic-grade procurement workspace. Upload, analyze, and propose — powered by your choice of AI.'}
              </p>
            </div>
            <ul className="space-y-4 text-sm text-white/85">
              <li className="flex items-center gap-3">
                <Upload className="h-4 w-4 opacity-80" />
                Document upload &amp; extraction
              </li>
              <li className="flex items-center gap-3">
                <FileSearch className="h-4 w-4 opacity-80" />
                AI requirement analysis
              </li>
              <li className="flex items-center gap-3">
                <Sparkles className="h-4 w-4 opacity-80" />
                OpenAI · Anthropic · Gemini · Ollama
              </li>
            </ul>
          </div>
          <p className="relative z-10 text-xs text-white/50">
            {branding.auth_tagline || 'Secure workspace login'}
          </p>
        </div>

        <div className="auth-form-panel flex items-center justify-center">
          <div className="glass-panel-strong w-full max-w-md p-8 md:p-10">
            <h2 className="font-display text-2xl font-semibold tracking-tight">Welcome back</h2>
            <p className="mt-2 text-sm text-muted-foreground">Sign in to your workspace.</p>

            <form onSubmit={handleSubmit} className="mt-6 space-y-5">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  autoComplete="email"
                  className="h-11 border-white/10 bg-background/50"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="password">Password</Label>
                  <Link href="/forgot-password" className="text-xs text-primary hover:underline">
                    Forgot?
                  </Link>
                </div>
                <PasswordInput
                  id="password"
                  autoComplete="current-password"
                  className="h-11 border-white/10 bg-background/50"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
              {error && (
                <p className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                  {error}
                </p>
              )}
              <Button type="submit" className="btn-cinematic h-11 w-full" disabled={submitting}>
                {submitting ? 'Signing in…' : 'Sign in'}
              </Button>
            </form>

            <p className="mt-6 text-center text-sm text-muted-foreground">
              No account?{' '}
              <Link href="/sign-up" className="font-medium text-primary hover:underline">
                Create one
              </Link>
            </p>

            {clerkEnabled && ClerkView && (
              <div className="mt-8 border-t border-white/10 pt-6">
                <ClerkView />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
