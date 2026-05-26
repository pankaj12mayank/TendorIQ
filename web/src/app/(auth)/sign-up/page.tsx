'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useState, type ComponentType } from 'react';
import { Sparkles } from 'lucide-react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { PasswordInput } from '@/components/ui/password-input';
import { exchangeSupabaseSession } from '@/lib/auth-api';
import { getPostLoginPath } from '@/lib/auth-redirect';
import { setStoredSession } from '@/lib/auth-session';
import { isClerkConfigured } from '@/lib/clerk-config';
import { getAuthProvider, isSupabaseConfigured } from '@/lib/supabase-config';
import { getSupabaseBrowserClient } from '@/lib/supabase/client';

export default function SignUpPage() {
  const router = useRouter();
  const provider = getAuthProvider();
  const supabaseEnabled = provider === 'supabase' && isSupabaseConfigured();
  const clerkEnabled = provider === 'clerk' && isClerkConfigured();
  const [ClerkView, setClerkView] = useState<ComponentType | null>(null);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!clerkEnabled) return;
    void import('./sign-up-clerk').then((m) => setClerkView(() => m.default));
  }, [clerkEnabled]);

  async function handleSupabaseSignUp(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    const supabase = getSupabaseBrowserClient();
    if (!supabase) {
      setError('Supabase is not configured');
      setSubmitting(false);
      return;
    }
    try {
      const { data, error: signUpError } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: { full_name: name || undefined },
          emailRedirectTo: `${window.location.origin}/sign-in`,
        },
      });
      if (signUpError) throw new Error(signUpError.message);
      const token = data.session?.access_token;
      if (token) {
        const exchanged = await exchangeSupabaseSession(token);
        if (exchanged) {
          setStoredSession(exchanged.token, exchanged.user, {
            refreshToken: exchanged.refreshToken,
            expiresInSec: exchanged.expiresIn,
          });
          toast.success('Account created');
          router.push(getPostLoginPath(exchanged.user.role));
          return;
        }
      }
      toast.success('Check your email to confirm your account, then sign in.');
      router.push('/sign-in');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sign up failed');
    } finally {
      setSubmitting(false);
    }
  }

  if (supabaseEnabled) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-background to-muted/30 p-6">
        <div className="w-full max-w-md space-y-6 rounded-2xl border bg-card p-8 shadow-lg">
          <div>
            <h1 className="text-xl font-semibold">Create your TenderIQ account</h1>
            <p className="text-sm text-muted-foreground">Sign up with email and password (Supabase Auth).</p>
          </div>
          <form onSubmit={handleSupabaseSignUp} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Name</Label>
              <Input id="name" value={name} onChange={(e) => setName(e.target.value)} />
            </div>
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
              <Label htmlFor="password">Password</Label>
              <PasswordInput
                id="password"
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
              />
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button type="submit" className="w-full" disabled={submitting}>
              {submitting ? 'Creating account...' : 'Sign up'}
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
      <div className="mx-auto max-w-lg space-y-4">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10">
          <Sparkles className="h-7 w-7 text-primary" />
        </div>
        <h1 className="text-2xl font-semibold">Get started with TenderIQ</h1>
        <p className="text-muted-foreground">
          Configure Supabase (`NEXT_PUBLIC_SUPABASE_URL` + anon key) or use demo credentials on the
          sign-in page for local development.
        </p>
      </div>
      <div className="flex flex-wrap justify-center gap-3">
        <Button asChild>
          <Link href="/sign-in">Sign in</Link>
        </Button>
        <Button asChild variant="outline">
          <Link href="/">Home</Link>
        </Button>
      </div>
    </div>
  );
}
