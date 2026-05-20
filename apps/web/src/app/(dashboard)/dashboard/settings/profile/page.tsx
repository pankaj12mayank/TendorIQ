'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useCurrentUser } from '@/hooks/use-auth';

export default function ProfileSettingsPage() {
  const user = useCurrentUser();

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
    </div>
  );
}
