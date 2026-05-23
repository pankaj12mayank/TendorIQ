'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Building2, Loader2 } from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { api } from '@/lib/api-client';
import { parseOrganizationsList, type OrganizationRow } from '@/lib/organizations-api';
import { ROUTES } from '@/lib/routes';
import { useCurrentUser } from '@/hooks/use-auth';
import { useTenantStore } from '@/stores/tenant-store';

export default function OrganizationsPage() {
  const user = useCurrentUser();
  const setCurrentOrganization = useTenantStore((s) => s.setCurrentOrganization);
  const [orgs, setOrgs] = useState<OrganizationRow[]>([]);
  const [isLoading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const res = await api.get<unknown>('/api/v1/organizations');
        if (!cancelled) setOrgs(parseOrganizationsList(res));
      } catch {
        if (!cancelled) setError('Failed to load organization');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const active = orgs[0];

  useEffect(() => {
    if (active) {
      setCurrentOrganization({
        id: active.id,
        name: active.name,
        slug: active.slug,
        role: 'admin',
      });
    }
  }, [active, setCurrentOrganization]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Team & organization</h1>
        <p className="text-sm text-muted-foreground">
          Workspace tied to your tenant membership ({user?.email ?? '—'}).
        </p>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : error ? (
        <p className="text-sm text-destructive">{error}</p>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Building2 className="h-5 w-5" />
              {active?.name ?? 'Organization'}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div>
              <p className="text-muted-foreground">Slug</p>
              <p className="font-medium">{active?.slug ?? '—'}</p>
            </div>
            {active?.description && (
              <div>
                <p className="text-muted-foreground">Description</p>
                <p>{active.description}</p>
              </div>
            )}
            {active?.website && (
              <div>
                <p className="text-muted-foreground">Website</p>
                <a href={active.website} className="text-primary hover:underline" target="_blank" rel="noreferrer">
                  {active.website}
                </a>
              </div>
            )}
            <Button variant="outline" asChild>
              <Link href={ROUTES.settingsProfile}>Profile settings</Link>
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
