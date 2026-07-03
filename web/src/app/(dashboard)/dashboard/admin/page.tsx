'use client';

import { useEffect, useState } from 'react';
import { BarChart3, CreditCard, DollarSign, Users, Upload } from 'lucide-react';

import { AdminRouteGuard } from '@/components/auth/admin-route-guard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { KpiCard } from '@/components/design-system/kpi-card';
import { useAdminPlatform } from '@/hooks/use-admin-platform';

export default function AdminOverviewPage() {
  const [stats, setStats] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);
  const { loadUploads, loadUsers } = useAdminPlatform();

  useEffect(() => {
    (async () => {
      try {
        const [uploads, users] = await Promise.all([
          loadUploads({ limit: 1 }),
          loadUsers({ limit: 1, include_deleted: 'true' }),
        ]);
        setStats({
          total_uploads: (uploads as any)?.pagination?.total ?? 0,
          total_users: (users as any)?.pagination?.total ?? 0,
        });
      } catch { /* ignore */ }
      setLoading(false);
    })();
  }, [loadUploads, loadUsers]);

  return (
    <AdminRouteGuard>
      <div className="w-full space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Admin overview</h1>
            <p className="text-sm text-muted-foreground mt-1">Platform analytics and management</p>
          </div>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <KpiCard title="Total uploads" value={String(stats.total_uploads)} icon={Upload} />
          <KpiCard title="Total users" value={String(stats.total_users)} icon={Users} />
          <KpiCard title="Active subscriptions" value="—" icon={CreditCard} />
          <KpiCard title="Revenue (MTD)" value="—" icon={DollarSign} />
        </div>
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Quick links
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
              {[
                { label: 'Owner profile', href: '/dashboard/admin/owner' },
                { label: 'User management', href: '/dashboard/admin/users' },
                { label: 'Payment gateways', href: '/dashboard/admin/payments' },
                { label: 'Pricing plan', href: '/dashboard/admin/pricing' },
                { label: 'SMTP settings', href: '/dashboard/admin/smtp' },
                { label: 'Upload history', href: '/dashboard/admin/uploads' },
                { label: 'Analytics', href: '/dashboard/admin/analytics' },
              ].map((link) => (
                <a
                  key={link.href}
                  href={link.href}
                  className="rounded-lg border p-3 text-sm font-medium hover:bg-muted/50 transition-colors"
                >
                  {link.label}
                </a>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </AdminRouteGuard>
  );
}