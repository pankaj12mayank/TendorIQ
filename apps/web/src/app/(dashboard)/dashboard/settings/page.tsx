'use client';

import { useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { CreditCard, Gauge, User } from 'lucide-react';

import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useCurrentUser } from '@/hooks/use-auth';
import { isSuperAdmin } from '@/lib/permissions';
import { ROUTES } from '@/lib/routes';
import { LoadingState } from '@/components/ui/loading-state';

const SETTINGS_LINKS = [
  {
    title: 'Profile',
    description: 'Account details and SSO configuration',
    href: ROUTES.settingsProfile,
    icon: User,
  },
  {
    title: 'Usage',
    description: 'Plan limits and feature consumption',
    href: ROUTES.usage,
    icon: Gauge,
  },
  {
    title: 'Billing',
    description: 'Subscription and payment methods',
    href: ROUTES.billing,
    icon: CreditCard,
  },
] as const;

export default function SettingsPage() {
  const user = useCurrentUser();
  const router = useRouter();

  useEffect(() => {
    if (user && isSuperAdmin(user.role)) {
      router.replace('/dashboard/admin?module=ai_settings');
    }
  }, [user, router]);

  if (!user) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <LoadingState message="Loading settings..." />
      </div>
    );
  }

  if (isSuperAdmin(user.role)) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <LoadingState message="Opening platform settings..." />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">Manage your workspace profile, usage, and billing.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {SETTINGS_LINKS.map(({ title, description, href, icon: Icon }) => (
          <Link key={href} href={href} className="block transition-opacity hover:opacity-90">
            <Card className="h-full">
              <CardHeader>
                <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
                  <Icon className="h-5 w-5" />
                </div>
                <CardTitle className="text-lg">{title}</CardTitle>
                <CardDescription>{description}</CardDescription>
              </CardHeader>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
