'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { CheckCircle2 } from 'lucide-react';
import { appToast } from '@/lib/app-toast';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { PasswordInput } from '@/components/ui/password-input';
import { resetPasswordWithToken, validatePasswordResetToken } from '@/lib/auth-api';

export default function ResetPasswordPage() {
  const params = useSearchParams();
  const router = useRouter();
  const token = useMemo(() => params.get('token') ?? '', [params]);
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [validating, setValidating] = useState(true);
  const [tokenError, setTokenError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function run() {
      if (!token) {
        setTokenError('Missing reset token');
        setValidating(false);
        return;
      }
      setValidating(true);
      try {
        await validatePasswordResetToken(token);
        if (!cancelled) setTokenError(null);
      } catch (err) {
        if (!cancelled) {
          setTokenError(err instanceof Error ? err.message : 'Invalid or expired reset token');
        }
      } finally {
        if (!cancelled) setValidating(false);
      }
    }
    void run();
    return () => {
      cancelled = true;
    };
  }, [token]);

  const canSubmit =
    !!password &&
    password.length >= 8 &&
    confirmPassword.length >= 8 &&
    password === confirmPassword &&
    !submitting &&
    !validating &&
    !tokenError;

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;
    setSubmitting(true);
    try {
      await resetPasswordWithToken(token, password);
      setDone(true);
      appToast.success('Password reset successful.');
    } catch (err) {
      appToast.error(err instanceof Error ? err.message : 'Failed to reset password');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Set new password</CardTitle>
          <CardDescription>
            {done
              ? 'Password updated successfully.'
              : 'Enter and confirm your new password (minimum 8 characters).'}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {validating && <p className="text-sm text-muted-foreground">Validating reset link...</p>}

          {!validating && tokenError && (
            <div className="space-y-3">
              <p className="text-sm text-destructive">{tokenError}</p>
              <Button asChild className="w-full" variant="outline">
                <Link href="/forgot-password">Request new reset link</Link>
              </Button>
            </div>
          )}

          {!validating && !tokenError && !done && (
            <form onSubmit={onSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="new-password">New password</Label>
                <PasswordInput
                  id="new-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="confirm-password">Confirm password</Label>
                <PasswordInput
                  id="confirm-password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                />
              </div>
              {confirmPassword && password !== confirmPassword && (
                <p className="text-xs text-destructive">Passwords do not match</p>
              )}
              <Button type="submit" className="w-full" disabled={!canSubmit}>
                {submitting ? 'Updating...' : 'Update password'}
              </Button>
            </form>
          )}

          {done && (
            <div className="space-y-4">
              <div className="flex items-center justify-center gap-2 text-success">
                <CheckCircle2 className="h-5 w-5" />
                <span className="text-sm font-medium">Password updated</span>
              </div>
              <Button
                className="w-full"
                onClick={() => router.push('/sign-in')}
              >
                Go to sign in
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
