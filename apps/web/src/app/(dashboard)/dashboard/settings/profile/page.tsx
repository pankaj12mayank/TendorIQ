'use client';

import { useEffect } from 'react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useCurrentUser } from '@/hooks/use-auth';
import { useSsoAdmin } from '@/hooks/use-sso';

export default function ProfileSettingsPage() {
  const user = useCurrentUser();
  const { config, isLoading, error, fetchConfig } = useSsoAdmin();

  useEffect(() => {
    void fetchConfig().catch(() => undefined);
  }, [fetchConfig]);

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold">Profile</h1>
      <Card>
        <CardHeader>
          <CardTitle>Account</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div>
            <p className="text-muted-foreground">Name</p>
            <p className="font-medium">{user?.name ?? '—'}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Email</p>
            <p className="font-medium">{user?.email ?? '—'}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Role</p>
            <p className="font-medium capitalize">{user?.role?.replace('_', ' ') ?? '—'}</p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Enterprise SSO</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          {isLoading && <p className="text-muted-foreground">Loading SSO settings...</p>}
          {error && <p className="text-destructive">{error}</p>}
          {!isLoading && !error && (
            <>
              <p>
                <span className="text-muted-foreground">Status: </span>
                <span className="font-medium">{config?.enabled ? 'Enabled' : 'Disabled'}</span>
              </p>
              <p>
                <span className="text-muted-foreground">Provider: </span>
                <span className="font-medium">{config?.provider ?? 'none'}</span>
              </p>
              <p className="text-muted-foreground">
                Configure SSO under organization settings (requires org:update). Sign-in URL:{' '}
                <code className="text-xs">/sign-in?org=&lt;slug&gt;</code>
              </p>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
