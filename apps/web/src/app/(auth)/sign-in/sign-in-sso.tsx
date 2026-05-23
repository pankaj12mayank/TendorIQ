'use client';

import { useEffect, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useSsoSignIn } from '@/hooks/use-sso';
import { getPostLoginPath } from '@/lib/auth-redirect';
import { useRouter } from 'next/navigation';

interface SignInSsoProps {
  orgSlug: string;
}

/** Enterprise SSO sign-in for `?org=<slug>` (dev token: work email). */
export default function SignInSso({ orgSlug }: SignInSsoProps) {
  const router = useRouter();
  const { publicConfig, isLoading, error, loadPublicConfig, signInWithToken } =
    useSsoSignIn(orgSlug);
  const [token, setToken] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    void loadPublicConfig(orgSlug);
  }, [orgSlug, loadPublicConfig]);

  if (isLoading && !publicConfig) {
    return <p className="text-sm text-muted-foreground">Loading SSO for {orgSlug}...</p>;
  }

  if (!publicConfig?.enabled) {
    return (
      <p className="text-sm text-muted-foreground">
        SSO is not enabled for <span className="font-medium">{orgSlug}</span>. Use email sign-in
        above.
      </p>
    );
  }

  async function handleSsoSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      const user = await signInWithToken(orgSlug, token);
      if (user) {
        router.replace(getPostLoginPath(user.membershipRole ?? user.role));
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSsoSubmit} className="space-y-3">
      <p className="text-sm text-muted-foreground">
        Sign in with {publicConfig.provider} for <span className="font-medium">{orgSlug}</span>
      </p>
      <div className="space-y-2">
        <Label htmlFor="sso-token">SSO token or work email (dev)</Label>
        <Input
          id="sso-token"
          type="text"
          autoComplete="email"
          placeholder="you@company.com"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          required
        />
      </div>
      {error && <p className="text-sm text-destructive">{error}</p>}
      <Button type="submit" variant="outline" className="w-full" disabled={submitting}>
        {submitting ? 'Signing in...' : 'Continue with SSO'}
      </Button>
    </form>
  );
}
