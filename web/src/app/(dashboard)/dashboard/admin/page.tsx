'use client';

import { useCallback, useEffect, useState } from 'react';
import { toast } from 'sonner';

import { AdminRouteGuard } from '@/components/auth/admin-route-guard';
import { PageHeader } from '@/components/design-system/page-header';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { LoadingState } from '@/components/ui/loading-state';
import { authenticatedJson } from '@/lib/api-fetch';
import {
  useAdminPlatform,
  type AdminUpload,
  type PlatformSettings,
} from '@/hooks/use-admin-platform';

type PlatformUser = {
  id: string;
  name: string;
  email: string;
  role: string;
  organization: string;
};

type UsageSummary = {
  total_users: number;
  total_actions: number;
  ai_tokens_used: number;
};

type Tab = 'overview' | 'users' | 'pricing' | 'ai' | 'landing' | 'uploads';

export default function AdminDashboardPage() {
  const [tab, setTab] = useState<Tab>('overview');
  const [users, setUsers] = useState<PlatformUser[]>([]);
  const [usage, setUsage] = useState<UsageSummary | null>(null);
  const [uploads, setUploads] = useState<AdminUpload[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { settings, saving, loadSettings, saveSection, loadUploads } = useAdminPlatform();

  const [pricingJson, setPricingJson] = useState('');
  const [aiJson, setAiJson] = useState('');
  const [landingJson, setLandingJson] = useState('');
  const [demoJson, setDemoJson] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const [usersRes, usageRes] = await Promise.all([
          authenticatedJson<{ data: PlatformUser[] }>('/api/v1/admin/platform/users'),
          authenticatedJson<{ data: UsageSummary }>('/api/v1/admin/platform/analytics/summary'),
        ]);
        setUsers(usersRes.data ?? []);
        setUsage(usageRes.data ?? null);
        const s = await loadSettings();
        syncEditors(s);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load admin data');
      } finally {
        setLoading(false);
      }
    })();
  }, [loadSettings]);

  const syncEditors = (s: PlatformSettings | null) => {
    if (!s) return;
    setPricingJson(JSON.stringify(s.pricing ?? {}, null, 2));
    setAiJson(JSON.stringify(s.ai_defaults ?? {}, null, 2));
    setLandingJson(JSON.stringify(s.landing ?? {}, null, 2));
    setDemoJson(JSON.stringify(s.demo_limits ?? {}, null, 2));
  };

  const loadUploadList = useCallback(async () => {
    const rows = await loadUploads();
    setUploads(rows);
  }, [loadUploads]);

  useEffect(() => {
    if (tab === 'uploads') void loadUploadList();
  }, [tab, loadUploadList]);

  const saveJsonSection = async (
    section: keyof PlatformSettings,
    raw: string
  ) => {
    try {
      const data = JSON.parse(raw) as Record<string, unknown>;
      await saveSection(section, data);
      toast.success(`${section} saved`);
    } catch {
      toast.error('Invalid JSON');
    }
  };

  const tabs: { id: Tab; label: string }[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'users', label: 'Users' },
    { id: 'pricing', label: 'Pricing' },
    { id: 'ai', label: 'AI defaults' },
    { id: 'landing', label: 'Landing CMS' },
    { id: 'uploads', label: 'Uploads' },
  ];

  return (
    <AdminRouteGuard>
      <div className="space-y-8">
        <PageHeader
          title="Platform admin"
          description="Users, pricing, AI defaults, landing CMS, and uploads. Super admin only."
        />

        <div className="tabs-pill-list max-w-4xl">
          {tabs.map((t) => (
            <Button
              key={t.id}
              variant="ghost"
              size="sm"
              className={
                tab === t.id
                  ? 'rounded-lg bg-background text-foreground shadow-sm hover:bg-background'
                  : 'rounded-lg text-muted-foreground'
              }
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </Button>
          ))}
        </div>

        {loading && <LoadingState message="Loading admin..." />}
        {error && <p className="text-sm text-destructive">{error}</p>}

        {!loading && tab === 'overview' && usage && (
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium">Users</CardTitle>
              </CardHeader>
              <CardContent className="text-2xl font-bold">{usage.total_users}</CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium">Actions</CardTitle>
              </CardHeader>
              <CardContent className="text-2xl font-bold">{usage.total_actions}</CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium">AI tokens</CardTitle>
              </CardHeader>
              <CardContent className="text-2xl font-bold">{usage.ai_tokens_used}</CardContent>
            </Card>
          </div>
        )}

        {!loading && tab === 'users' && (
          <Card>
            <CardHeader>
              <CardTitle>Users</CardTitle>
              <CardDescription>All registered users across workspaces</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="divide-y text-sm">
                {users.map((u) => (
                  <li key={u.id} className="flex justify-between py-2">
                    <span>
                      {u.name} &lt;{u.email}&gt; — {u.role}
                    </span>
                    <span className="text-muted-foreground">{u.organization}</span>
                  </li>
                ))}
                {users.length === 0 && <li className="text-muted-foreground">No users</li>}
              </ul>
            </CardContent>
          </Card>
        )}

        {!loading && tab === 'pricing' && (
          <Card>
            <CardHeader>
              <CardTitle>Pricing plans</CardTitle>
              <CardDescription>
                JSON: plans with id, name, monthly_inr, yearly_inr, features. Razorpay uses these
                amounts.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                className="min-h-[280px] font-mono text-xs"
                value={pricingJson}
                onChange={(e) => setPricingJson(e.target.value)}
              />
              <Button disabled={saving} onClick={() => void saveJsonSection('pricing', pricingJson)}>
                Save pricing
              </Button>
            </CardContent>
          </Card>
        )}

        {!loading && tab === 'ai' && (
          <Card>
            <CardHeader>
              <CardTitle>AI defaults</CardTitle>
              <CardDescription>Platform-wide hints: default_provider, default_model, etc.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                className="min-h-[200px] font-mono text-xs"
                value={aiJson}
                onChange={(e) => setAiJson(e.target.value)}
              />
              <Button disabled={saving} onClick={() => void saveJsonSection('ai_defaults', aiJson)}>
                Save AI settings
              </Button>
            </CardContent>
          </Card>
        )}

        {!loading && tab === 'landing' && (
          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Landing CMS</CardTitle>
                <CardDescription>hero, faq, cta — served at GET /api/v1/public/site</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Textarea
                  className="min-h-[320px] font-mono text-xs"
                  value={landingJson}
                  onChange={(e) => setLandingJson(e.target.value)}
                />
                <Button
                  disabled={saving}
                  onClick={() => void saveJsonSection('landing', landingJson)}
                >
                  Save landing
                </Button>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Demo quotas</CardTitle>
                <CardDescription>Per-plan limits under demo_limits (e.g. free)</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Textarea
                  className="min-h-[200px] font-mono text-xs"
                  value={demoJson}
                  onChange={(e) => setDemoJson(e.target.value)}
                />
                <Button
                  disabled={saving}
                  onClick={() => void saveJsonSection('demo_limits', demoJson)}
                >
                  Save demo limits
                </Button>
              </CardContent>
            </Card>
          </div>
        )}

        {!loading && tab === 'uploads' && (
          <Card>
            <CardHeader>
              <CardTitle>Recent uploads</CardTitle>
              <CardDescription>Latest documents across all tenants</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="divide-y text-sm">
                {uploads.map((u) => (
                  <li key={u.id} className="flex flex-wrap justify-between gap-2 py-2">
                    <span>
                      {u.name} — {u.status}
                    </span>
                    <span className="text-muted-foreground">
                      {u.owner_email} · {u.tenant_name} · {new Date(u.created_at).toLocaleString()}
                    </span>
                  </li>
                ))}
                {uploads.length === 0 && <li className="text-muted-foreground">No uploads</li>}
              </ul>
            </CardContent>
          </Card>
        )}

        {settings && tab === 'overview' && (
          <p className="text-xs text-muted-foreground">
            Platform settings loaded. Use tabs to edit pricing, AI, landing, and demo limits.
          </p>
        )}
      </div>
    </AdminRouteGuard>
  );
}
