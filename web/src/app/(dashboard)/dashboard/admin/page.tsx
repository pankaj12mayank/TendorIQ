'use client';

import Link from 'next/link';
import { useCallback, useEffect, useState } from 'react';
import { FlaskConical, Upload } from 'lucide-react';
import { appToast } from '@/lib/app-toast';
import { ROUTES } from '@/lib/routes';

import { AdminRouteGuard } from '@/components/auth/admin-route-guard';
import { CmsControlPanel } from '@/components/admin/cms-control-panel';
import { DashboardIntelligence } from '@/components/dashboard/dashboard-intelligence';
import { PageHeader } from '@/components/design-system/page-header';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { LoadingState } from '@/components/ui/loading-state';
import { authenticatedJson } from '@/lib/api-fetch';
import {
  useAdminPlatform,
  type AdminUpload,
  type PlatformSettings,
  type PlatformUserRow,
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
  active_users: number;
  uploads_total: number;
  ai_jobs_total: number;
  failed_ai_jobs: number;
  revenue: number;
  total_actions: number;
  ai_tokens_used: number;
};

type Tab =
  | 'overview'
  | 'owner'
  | 'users'
  | 'payments'
  | 'pricing'
  | 'ai'
  | 'cms'
  | 'smtp'
  | 'uploads'
  | 'analytics';
type UserStatusFilter = 'all' | 'active' | 'inactive';

function JsonEditor({
  label,
  help,
  value,
  onChange,
  onSave,
  saving,
  minHeight = 'min-h-[220px]',
}: {
  label: string;
  help: string;
  value: string;
  onChange: (v: string) => void;
  onSave: () => Promise<void> | void;
  saving?: boolean;
  minHeight?: string;
}) {
  return (
    <div className="space-y-3 rounded-lg border border-border/70 bg-muted/10 p-3 sm:p-4">
      <div className="space-y-1">
        <p className="text-sm font-medium">{label}</p>
        <p className="text-xs text-muted-foreground">{help}</p>
      </div>
      <Textarea
        aria-label={`${label} JSON editor`}
        className={`${minHeight} font-mono text-xs`}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
      <Button loading={saving} disabled={saving} onClick={() => void onSave()}>
        Save {label.toLowerCase()}
      </Button>
    </div>
  );
}

export default function AdminDashboardPage() {
  const [tab, setTab] = useState<Tab>('overview');
  const [users, setUsers] = useState<PlatformUserRow[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [selectedUserDetail, setSelectedUserDetail] = useState<Record<string, unknown> | null>(null);
  const [userSearch, setUserSearch] = useState('');
  const [userStatusFilter, setUserStatusFilter] = useState<UserStatusFilter>('all');
  const [usersPage, setUsersPage] = useState(1);
  const [usersMeta, setUsersMeta] = useState<{ page: number; pages: number; total: number; limit: number }>({
    page: 1,
    pages: 0,
    total: 0,
    limit: 25,
  });
  const [usage, setUsage] = useState<UsageSummary | null>(null);
  const [uploads, setUploads] = useState<AdminUpload[]>([]);
  const [uploadSearch, setUploadSearch] = useState('');
  const [uploadStatus, setUploadStatus] = useState('');
  const [uploadUserFilter, setUploadUserFilter] = useState('');
  const [selectedUploads, setSelectedUploads] = useState<string[]>([]);
  const [paymentSettings, setPaymentSettings] = useState<Record<string, unknown>>({});
  const [paymentHistory, setPaymentHistory] = useState<Record<string, unknown> | null>(null);
  const [paymentStatusFilter, setPaymentStatusFilter] = useState('all');
  const [paymentProviderFilter, setPaymentProviderFilter] = useState('all');
  const [paymentPage, setPaymentPage] = useState(1);
  const [analyticsQuery, setAnalyticsQuery] = useState('');
  const [analyticsRows, setAnalyticsRows] = useState<Record<string, unknown>[]>([]);
  const [ownerProfile, setOwnerProfile] = useState<Record<string, unknown> | null>(null);
  const [ownerPassword, setOwnerPassword] = useState('');
  const [ownerUsername, setOwnerUsername] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const {
    settings,
    saving,
    loadSettings,
    saveSection,
    loadUploads,
    loadUsers,
    loadUserDetail,
    updateUserStatus,
    deleteUser,
    loadOwnerProfile,
    saveOwnerProfile,
    uploadOwnerAsset,
    loadSmtpSettings,
    saveSmtpSettings,
    testSmtpSettings,
    loadPaymentSettings,
    savePaymentSettings,
    testPaymentSettings,
    loadPaymentHistory,
    saveBillingPricing,
    searchAnalyticsUser,
    deleteUpload,
    batchDeleteUploads,
  } = useAdminPlatform();

  const [pricingJson, setPricingJson] = useState('');
  const [aiJson, setAiJson] = useState('');
  const [smtp, setSmtp] = useState({
    host: '',
    port: 587,
    sender_email: '',
    sender_name: 'TenderIQ',
    app_password: '',
  });
  const [smtpTestEmail, setSmtpTestEmail] = useState('');
  const [smtpTesting, setSmtpTesting] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const [usersRes, usageRes, ownerRes, paymentCfg] = await Promise.all([
          loadUsers({ page: 1, limit: 25, include_deleted: true }),
          authenticatedJson<{ data: UsageSummary }>('/api/v1/admin/platform/analytics/summary'),
          loadOwnerProfile(),
          loadPaymentSettings(),
        ]);
        setUsers(usersRes.rows ?? []);
        setUsage(usageRes.data ?? null);
        setOwnerProfile(ownerRes);
        setOwnerUsername(String(ownerRes.username ?? ''));
        setPaymentSettings(paymentCfg);
        const s = await loadSettings();
        syncEditors(s);
        const smtpLoaded = await loadSmtpSettings();
        setSmtp({
          host: String(smtpLoaded.host ?? ''),
          port: Number(smtpLoaded.port ?? 587),
          sender_email: String(smtpLoaded.sender_email ?? ''),
          sender_name: String(smtpLoaded.sender_name ?? 'TenderIQ'),
          app_password: String(smtpLoaded.app_password ?? ''),
        });
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load admin data');
      } finally {
        setLoading(false);
      }
    })();
  }, [loadSettings, loadSmtpSettings, loadUsers, loadOwnerProfile, loadPaymentSettings]);

  const syncEditors = (s: PlatformSettings | null) => {
    if (!s) return;
    setPricingJson(JSON.stringify(s.pricing ?? {}, null, 2));
    setAiJson(JSON.stringify(s.ai_defaults ?? {}, null, 2));
  };

  const loadUploadList = useCallback(async () => {
    const rows = await loadUploads({
      limit: 100,
      search: uploadSearch || undefined,
      status: uploadStatus || undefined,
      user_filter: uploadUserFilter || undefined,
    });
    setUploads(rows);
  }, [loadUploads, uploadSearch, uploadStatus, uploadUserFilter]);

  const fetchUsers = useCallback(async () => {
    const params: Record<string, string | number | boolean> = {
      search: userSearch,
      page: usersPage,
      limit: usersMeta.limit,
      include_deleted: true,
    };
    if (userStatusFilter === 'active' || userStatusFilter === 'inactive') {
      params.status = userStatusFilter;
    }
    const out = await loadUsers(params);
    const pagination = (out.pagination ?? {}) as Record<string, unknown>;
    setUsersMeta((prev) => ({
      ...prev,
      page: Number(pagination.page ?? usersPage),
      pages: Number(pagination.pages ?? 0),
      total: Number(pagination.total ?? 0),
      limit: Number(pagination.limit ?? prev.limit),
    }));
    let rows = out.rows;
    if (userStatusFilter === 'all') {
      rows = rows;
    } else {
      rows = rows.filter((u) => u.status === userStatusFilter);
    }
    setUsers(rows);
  }, [loadUsers, userSearch, userStatusFilter, usersPage, usersMeta.limit]);

  useEffect(() => {
    if (tab === 'uploads') void loadUploadList();
  }, [tab, loadUploadList]);

  useEffect(() => {
    setUsersPage(1);
  }, [userSearch, userStatusFilter]);

  const loadPayments = useCallback(async () => {
    const hist = (await loadPaymentHistory({
      page: paymentPage,
      limit: 25,
      status: paymentStatusFilter === 'all' ? undefined : paymentStatusFilter,
      provider: paymentProviderFilter === 'all' ? undefined : paymentProviderFilter,
    })) as Record<string, unknown>;
    setPaymentHistory(hist);
  }, [loadPaymentHistory, paymentPage, paymentProviderFilter, paymentStatusFilter]);

  useEffect(() => {
    if (loading || tab !== 'users') return;
    void fetchUsers();
  }, [loading, tab, fetchUsers]);

  useEffect(() => {
    if (loading || tab !== 'payments') return;
    void loadPayments();
  }, [loading, tab, loadPayments]);

  const tabs: { id: Tab; label: string }[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'owner', label: 'Owner' },
    { id: 'users', label: 'Users' },
    { id: 'payments', label: 'Payments' },
    { id: 'pricing', label: 'Pricing' },
    { id: 'ai', label: 'AI Settings' },
    { id: 'cms', label: 'CMS Control' },
    { id: 'smtp', label: 'SMTP' },
    { id: 'uploads', label: 'Uploads' },
    { id: 'analytics', label: 'Analytics' },
  ];

  return (
    <AdminRouteGuard>
      <div className="mx-auto w-full max-w-7xl space-y-6 app-section">
        <PageHeader
          title="Platform admin"
          description="Manage users, pricing, landing content, payments, and platform operations."
        />

        <Card className="border-primary/25 bg-primary/5">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-base">
              <FlaskConical className="h-5 w-5 text-primary" />
              Test customer flow
            </CardTitle>
            <CardDescription>
              Preview upload, analysis, proposal, and billing exactly as a paying customer. Use the
              sidebar section &quot;Test customer flow&quot; or start with Upload.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild>
              <Link href={ROUTES.upload}>
                <Upload className="mr-2 h-4 w-4" />
                Open customer Upload
              </Link>
            </Button>
          </CardContent>
        </Card>

        <div
          className="tabs-pill-list flex flex-wrap gap-2 rounded-xl border border-border/60 bg-muted/20 p-2"
          role="tablist"
          aria-label="Admin modules"
        >
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
              disabled={loading}
              role="tab"
              aria-selected={tab === t.id}
              aria-controls={`admin-panel-${t.id}`}
              id={`admin-tab-${t.id}`}
            >
              {t.label}
            </Button>
          ))}
        </div>

        {loading && <LoadingState message="Loading admin..." />}
        {error && <p className="text-sm text-destructive">{error}</p>}

        {!loading && tab === 'overview' && <DashboardIntelligence />}
        {!loading && tab === 'cms' && <CmsControlPanel />}

        {!loading && tab === 'owner' && (
          <Card>
            <CardHeader>
              <CardTitle>System owner profile</CardTitle>
              <CardDescription>Update username/password and branding assets.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label>Username</Label>
                  <Input value={ownerUsername} onChange={(e) => setOwnerUsername(e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label>New password</Label>
                  <Input
                    type="password"
                    value={ownerPassword}
                    onChange={(e) => setOwnerPassword(e.target.value)}
                  />
                </div>
              </div>
              <Button
                loading={saving}
                disabled={saving}
                onClick={async () => {
                  const toastId = appToast.loading('Saving owner profile...');
                  await saveOwnerProfile({
                    username: ownerUsername,
                    ...(ownerPassword ? { password: ownerPassword } : {}),
                  });
                  setOwnerPassword('');
                  appToast.dismiss(toastId);
                  appToast.success('Owner profile updated.');
                  const latest = await loadOwnerProfile();
                  setOwnerProfile(latest);
                }}
              >
                Save owner profile
              </Button>
              <div className="grid gap-2 md:grid-cols-3">
                {(['avatar', 'logo', 'favicon'] as const).map((kind) => (
                  <div key={kind} className="space-y-2 rounded-md border p-3">
                    <Label className="capitalize">{kind} upload</Label>
                    <Input
                      type="file"
                      accept="image/*"
                      onChange={async (e) => {
                        const f = e.target.files?.[0];
                        if (!f) return;
                        try {
                          await uploadOwnerAsset(kind, f);
                          const latest = await loadOwnerProfile();
                          setOwnerProfile(latest);
                          appToast.success(`${kind} updated.`);
                        } catch (err) {
                          appToast.error(err instanceof Error ? err.message : 'Upload failed');
                        }
                      }}
                    />
                    {Boolean(ownerProfile?.[`${kind}_url`]) && (
                      <img
                        src={String(ownerProfile[`${kind}_url`])}
                        alt={kind}
                        className="h-10 w-10 rounded object-cover"
                      />
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {!loading && tab === 'users' && (
          <Card id="admin-panel-users" role="tabpanel" aria-labelledby="admin-tab-users">
            <CardHeader>
              <CardTitle>Users</CardTitle>
              <CardDescription>All registered users across workspaces</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="mb-3 flex gap-2">
                <Input
                  placeholder="Search user..."
                  value={userSearch}
                  onChange={(e) => setUserSearch(e.target.value)}
                />
                <Button
                  variant="outline"
                  onClick={async () => {
                    await fetchUsers();
                  }}
                >
                  Search
                </Button>
              </div>
              <div className="mb-3 flex flex-wrap gap-2">
                {(['all', 'active', 'inactive'] as UserStatusFilter[]).map((chip) => (
                  <Button
                    key={chip}
                    size="sm"
                    variant={userStatusFilter === chip ? 'default' : 'outline'}
                    onClick={async () => {
                      setUserStatusFilter(chip);
                    }}
                  >
                    {chip === 'all'
                      ? 'All'
                      : chip === 'active'
                        ? 'Active'
                          : 'Inactive'}
                  </Button>
                ))}
              </div>
              <ul className="divide-y text-sm">
                {users.map((u) => (
                  <li key={u.id} className="flex flex-col gap-2 py-3 md:flex-row md:items-center md:justify-between">
                    <span className="break-words">
                      {u.name} &lt;{u.email}&gt; — {u.role} · {u.plan ?? 'free'}
                    </span>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-muted-foreground">{u.organization}</span>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={async () => {
                          const next = u.status === 'active' ? 'inactive' : 'active';
                          await updateUserStatus(u.id, next);
                          await fetchUsers();
                          appToast.success(`User ${next === 'inactive' ? 'suspended' : 'activated'}.`);
                        }}
                      >
                        {u.status === 'active' ? 'Suspend' : 'Activate'}
                      </Button>
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={async () => {
                          if (!confirm(`Permanently delete user ${u.email}? This cannot be undone.`)) return;
                          await deleteUser(u.id);
                          await fetchUsers();
                          if (selectedUserId === u.id) {
                            setSelectedUserId(null);
                            setSelectedUserDetail(null);
                          }
                          appToast.success('User permanently deleted.');
                        }}
                      >
                        Delete
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={async () => {
                          const d = await loadUserDetail(u.id);
                          setSelectedUserId(u.id);
                          setSelectedUserDetail(d);
                        }}
                      >
                        Details
                      </Button>
                    </div>
                  </li>
                ))}
                {users.length === 0 && <li className="text-muted-foreground">No users</li>}
              </ul>
              {usersMeta.pages > 1 && (
                <div className="mt-3 flex items-center gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={usersPage <= 1}
                    onClick={() => setUsersPage((p) => Math.max(1, p - 1))}
                  >
                    Prev
                  </Button>
                  <span className="text-xs text-muted-foreground">
                    {usersPage}/{usersMeta.pages} · {usersMeta.total} users
                  </span>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={usersPage >= usersMeta.pages}
                    onClick={() => setUsersPage((p) => Math.min(usersMeta.pages, p + 1))}
                  >
                    Next
                  </Button>
                </div>
              )}
              {selectedUserId && selectedUserDetail && (
                <div className="mt-4 grid gap-3 text-xs sm:grid-cols-2 lg:grid-cols-3">
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">Usage</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <pre className="max-h-[220px] whitespace-pre-wrap break-all overflow-auto scroll-premium">
                        {JSON.stringify((selectedUserDetail as any).usage ?? {}, null, 2)}
                      </pre>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">Uploads</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <pre className="max-h-[220px] whitespace-pre-wrap break-all overflow-auto scroll-premium">
                        {JSON.stringify((selectedUserDetail as any).uploads ?? [], null, 2)}
                      </pre>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">Analysis</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <pre className="max-h-[220px] whitespace-pre-wrap break-all overflow-auto scroll-premium">
                        {JSON.stringify((selectedUserDetail as any).analysis ?? [], null, 2)}
                      </pre>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">Proposals</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <pre className="max-h-[220px] whitespace-pre-wrap break-all overflow-auto scroll-premium">
                        {JSON.stringify((selectedUserDetail as any).proposals ?? [], null, 2)}
                      </pre>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">Payments</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <pre className="max-h-[220px] whitespace-pre-wrap break-all overflow-auto scroll-premium">
                        {JSON.stringify((selectedUserDetail as any).payments ?? [], null, 2)}
                      </pre>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">Activity</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <pre className="max-h-[220px] whitespace-pre-wrap break-all overflow-auto scroll-premium">
                        {JSON.stringify((selectedUserDetail as any).activity_timeline ?? [], null, 2)}
                      </pre>
                    </CardContent>
                  </Card>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {!loading && tab === 'pricing' && (
          <Card id="admin-panel-pricing" role="tabpanel" aria-labelledby="admin-tab-pricing">
            <CardHeader>
              <CardTitle>Pricing</CardTitle>
              <CardDescription>
                Keep one active plan. Amounts use USD only.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <JsonEditor
                label="Pricing"
                help="Use plans[] with one active plan. Set monthly_usd, upload_limit, and expiry_period_days."
                value={pricingJson}
                onChange={setPricingJson}
                saving={saving}
                minHeight="min-h-[300px]"
                onSave={async () => {
                  try {
                    const parsed = JSON.parse(pricingJson) as Record<string, unknown>;
                    await saveBillingPricing(parsed);
                    appToast.success('Pricing updated.');
                  } catch (e) {
                    appToast.error(e instanceof Error ? e.message : 'Pricing update failed');
                  }
                }}
              />
            </CardContent>
          </Card>
        )}

        {!loading && tab === 'ai' && (
          <Card id="admin-panel-ai" role="tabpanel" aria-labelledby="admin-tab-ai">
            <CardHeader>
              <CardTitle>AI settings</CardTitle>
              <CardDescription>
                Manage default provider/model values for platform-wide AI operations.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <JsonEditor
                label="AI settings"
                help="Edit ai_defaults JSON and save."
                value={aiJson}
                onChange={setAiJson}
                saving={saving}
                minHeight="min-h-[260px]"
                onSave={async () => {
                  try {
                    const parsed = JSON.parse(aiJson) as Record<string, unknown>;
                    await saveSection('ai_defaults', parsed);
                    appToast.success('AI settings updated.');
                  } catch (e) {
                    appToast.error(e instanceof Error ? e.message : 'AI settings update failed');
                  }
                }}
              />
            </CardContent>
          </Card>
        )}

        {!loading && tab === 'payments' && (
          <div className="space-y-6" id="admin-panel-payments" role="tabpanel" aria-labelledby="admin-tab-payments">
            <Card>
              <CardHeader>
                <CardTitle>Payment gateways</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-3 md:grid-cols-2">
                  <Input
                    placeholder="Razorpay key id"
                    value={String(paymentSettings.razorpay_key_id ?? '')}
                    onChange={(e) =>
                      setPaymentSettings((s) => ({ ...s, razorpay_key_id: e.target.value }))
                    }
                  />
                  <Input
                    placeholder="Razorpay key secret"
                    value={String(paymentSettings.razorpay_key_secret ?? '')}
                    onChange={(e) =>
                      setPaymentSettings((s) => ({ ...s, razorpay_key_secret: e.target.value }))
                    }
                  />
                  <Input
                    placeholder="Stripe publishable key"
                    value={String(paymentSettings.stripe_publishable_key ?? '')}
                    onChange={(e) =>
                      setPaymentSettings((s) => ({ ...s, stripe_publishable_key: e.target.value }))
                    }
                  />
                  <Input
                    placeholder="Stripe secret key"
                    value={String(paymentSettings.stripe_secret_key ?? '')}
                    onChange={(e) =>
                      setPaymentSettings((s) => ({ ...s, stripe_secret_key: e.target.value }))
                    }
                  />
                  <Input
                    placeholder="Stripe webhook secret"
                    value={String(paymentSettings.stripe_webhook_secret ?? '')}
                    onChange={(e) =>
                      setPaymentSettings((s) => ({ ...s, stripe_webhook_secret: e.target.value }))
                    }
                  />
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button
                    loading={saving}
                    disabled={saving}
                    onClick={async () => {
                      await savePaymentSettings(paymentSettings);
                      appToast.success('Payment settings saved.');
                    }}
                  >
                    Save gateway settings
                  </Button>
                  <Button variant="outline" onClick={() => void testPaymentSettings('razorpay')}>
                    Test Razorpay
                  </Button>
                  <Button variant="outline" onClick={() => void testPaymentSettings('stripe')}>
                    Test Stripe
                  </Button>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Payment history</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex flex-wrap gap-2">
                  <Input
                    placeholder="Status (paid/failed)"
                    value={paymentStatusFilter}
                    onChange={(e) => {
                      setPaymentStatusFilter(e.target.value || 'all');
                      setPaymentPage(1);
                    }}
                    className="max-w-xs"
                  />
                  <Input
                    placeholder="Provider (razorpay/stripe)"
                    value={paymentProviderFilter}
                    onChange={(e) => {
                      setPaymentProviderFilter(e.target.value || 'all');
                      setPaymentPage(1);
                    }}
                    className="max-w-xs"
                  />
                  <Button variant="outline" onClick={() => void loadPayments()}>
                    Apply filters
                  </Button>
                </div>
                {paymentHistory && (
                  <div className="space-y-3">
                    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                      <Card>
                        <CardContent className="pt-4 text-sm">
                          <p className="text-muted-foreground">Revenue</p>
                          <p className="text-xl font-semibold">
                            ${Number((paymentHistory as any).cards?.total_revenue ?? 0).toLocaleString('en-US')}
                          </p>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardContent className="pt-4 text-sm">
                          <p className="text-muted-foreground">Failed payments</p>
                          <p className="text-xl font-semibold">{Number((paymentHistory as any).cards?.failed_count ?? 0)}</p>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardContent className="pt-4 text-sm">
                          <p className="text-muted-foreground">Renewals</p>
                          <p className="text-xl font-semibold">{Number((paymentHistory as any).cards?.renewals_count ?? 0)}</p>
                        </CardContent>
                      </Card>
                    </div>
                    <ul className="max-h-[260px] divide-y overflow-auto rounded-md border text-xs scroll-premium">
                      {(((paymentHistory as any).data ?? []) as Array<any>).map((p) => (
                        <li key={String(p.id)} className="flex items-center justify-between gap-2 p-2">
                          <span>
                            {p.provider} · {p.plan || '—'} · ${Number(p.amount || 0).toLocaleString('en-US')}
                          </span>
                          <span className="text-muted-foreground">{p.status}</span>
                        </li>
                      ))}
                    </ul>
                    {Number((paymentHistory as any).pagination?.pages ?? 0) > 1 && (
                      <div className="flex items-center gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={paymentPage <= 1}
                          onClick={() => setPaymentPage((p) => Math.max(1, p - 1))}
                        >
                          Prev
                        </Button>
                        <span className="text-xs text-muted-foreground">
                          {paymentPage}/{Number((paymentHistory as any).pagination?.pages ?? 1)}
                        </span>
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={paymentPage >= Number((paymentHistory as any).pagination?.pages ?? 1)}
                          onClick={() =>
                            setPaymentPage((p) =>
                              Math.min(Number((paymentHistory as any).pagination?.pages ?? 1), p + 1)
                            )
                          }
                        >
                          Next
                        </Button>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}


        {!loading && tab === 'smtp' && (
          <Card id="admin-panel-smtp" role="tabpanel" aria-labelledby="admin-tab-smtp">
            <CardHeader>
              <CardTitle>SMTP settings</CardTitle>
              <CardDescription>
                Configure password reset delivery. Secrets are encrypted at rest.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="smtp-host">SMTP host</Label>
                  <Input
                    id="smtp-host"
                    value={smtp.host}
                    onChange={(e) => setSmtp((s) => ({ ...s, host: e.target.value }))}
                    placeholder="smtp.gmail.com"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="smtp-port">SMTP port</Label>
                  <Input
                    id="smtp-port"
                    type="number"
                    value={smtp.port}
                    onChange={(e) =>
                      setSmtp((s) => ({
                        ...s,
                        port: Number(e.target.value || 587),
                      }))
                    }
                  />
                </div>
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="smtp-sender-email">Sender email</Label>
                  <Input
                    id="smtp-sender-email"
                    type="email"
                    value={smtp.sender_email}
                    onChange={(e) =>
                      setSmtp((s) => ({ ...s, sender_email: e.target.value }))
                    }
                    placeholder="noreply@company.com"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="smtp-sender-name">Sender name</Label>
                  <Input
                    id="smtp-sender-name"
                    value={smtp.sender_name}
                    onChange={(e) =>
                      setSmtp((s) => ({ ...s, sender_name: e.target.value }))
                    }
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="smtp-app-password">App password</Label>
                <Input
                  id="smtp-app-password"
                  type="password"
                  value={smtp.app_password}
                  onChange={(e) =>
                    setSmtp((s) => ({ ...s, app_password: e.target.value }))
                  }
                  placeholder="App password / SMTP password"
                />
              </div>
              <div className="flex flex-wrap gap-2">
                <Button
                  loading={saving}
                  disabled={saving}
                  onClick={async () => {
                    try {
                      await saveSmtpSettings(smtp);
                      appToast.success('SMTP settings saved.');
                    } catch (e) {
                      appToast.error(e instanceof Error ? e.message : 'Failed to save SMTP settings');
                    }
                  }}
                >
                  Save SMTP
                </Button>
              </div>
              <div className="grid gap-2 rounded-md border p-3 md:grid-cols-[1fr_auto]">
                <Input
                  type="email"
                  placeholder="test@yourdomain.com"
                  value={smtpTestEmail}
                  onChange={(e) => setSmtpTestEmail(e.target.value)}
                />
                <Button
                  variant="outline"
                  disabled={smtpTesting || !smtpTestEmail}
                  onClick={async () => {
                    setSmtpTesting(true);
                    try {
                      await testSmtpSettings(smtpTestEmail);
                      appToast.success('SMTP test email sent.');
                    } catch (e) {
                      appToast.error(e instanceof Error ? e.message : 'SMTP test failed');
                    } finally {
                      setSmtpTesting(false);
                    }
                  }}
                >
                  {smtpTesting ? 'Testing...' : 'Send test email'}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {!loading && tab === 'uploads' && (
          <Card id="admin-panel-uploads" role="tabpanel" aria-labelledby="admin-tab-uploads">
            <CardHeader>
              <CardTitle>Recent uploads</CardTitle>
              <CardDescription>Latest documents across all tenants</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="mb-3 flex flex-wrap gap-2">
                <Input
                  placeholder="Search uploads..."
                  value={uploadSearch}
                  onChange={(e) => setUploadSearch(e.target.value)}
                  className="max-w-xs"
                />
                <Input
                  placeholder="Status (processing/failed/completed)"
                  value={uploadStatus}
                  onChange={(e) => setUploadStatus(e.target.value)}
                  className="max-w-xs"
                />
                <Input
                  placeholder="User email filter"
                  value={uploadUserFilter}
                  onChange={(e) => setUploadUserFilter(e.target.value)}
                  className="max-w-xs"
                />
                <Button variant="outline" onClick={() => void loadUploadList()}>
                  Refresh
                </Button>
                <Button
                  variant="destructive"
                  disabled={selectedUploads.length === 0}
                  onClick={async () => {
                    await batchDeleteUploads(selectedUploads);
                    setSelectedUploads([]);
                    await loadUploadList();
                    appToast.success('Selected uploads deleted.');
                  }}
                >
                  Delete selected
                </Button>
              </div>
              <ul className="divide-y text-sm">
                {uploads.map((u) => (
                  <li key={u.id} className="flex flex-col gap-2 py-3 md:flex-row md:items-center md:justify-between">
                    <span className="flex items-center gap-2">
                      <input
                        aria-label={`Select upload ${u.name}`}
                        type="checkbox"
                        checked={selectedUploads.includes(u.id)}
                        onChange={(e) =>
                          setSelectedUploads((prev) =>
                            e.target.checked
                              ? [...prev, u.id]
                              : prev.filter((id) => id !== u.id)
                          )
                        }
                      />
                      {u.name} — {u.status}
                    </span>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="break-words text-muted-foreground">
                        {u.owner_email} · {u.tenant_name} · {new Date(u.created_at).toLocaleString()}
                      </span>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={async () => {
                          await deleteUpload(u.id);
                          await loadUploadList();
                        }}
                      >
                        Delete
                      </Button>
                    </div>
                  </li>
                ))}
                {uploads.length === 0 && <li className="text-muted-foreground">No uploads</li>}
              </ul>
            </CardContent>
          </Card>
        )}

        {!loading && tab === 'analytics' && (
          <Card id="admin-panel-analytics" role="tabpanel" aria-labelledby="admin-tab-analytics">
            <CardHeader>
              <CardTitle>User analytics search</CardTitle>
              <CardDescription>
                Search any user and view uploads, tenders, proposals, payments, activity counts.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
                <Card>
                  <CardContent className="pt-4 text-sm">
                    <p className="text-muted-foreground">Uploads</p>
                    <p className="text-xl font-semibold">{usage?.uploads_total ?? 0}</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-4 text-sm">
                    <p className="text-muted-foreground">Users (active/total)</p>
                    <p className="text-xl font-semibold">
                      {usage?.active_users ?? 0}/{usage?.total_users ?? 0}
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-4 text-sm">
                    <p className="text-muted-foreground">Revenue</p>
                    <p className="text-xl font-semibold">${Number(usage?.revenue ?? 0).toLocaleString('en-US')}</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-4 text-sm">
                    <p className="text-muted-foreground">AI jobs</p>
                    <p className="text-xl font-semibold">{usage?.ai_jobs_total ?? 0}</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-4 text-sm">
                    <p className="text-muted-foreground">Failed AI jobs</p>
                    <p className="text-xl font-semibold">{usage?.failed_ai_jobs ?? 0}</p>
                  </CardContent>
                </Card>
              </div>
              <div className="flex gap-2">
                <Input
                  placeholder="Search by email or name"
                  value={analyticsQuery}
                  onChange={(e) => setAnalyticsQuery(e.target.value)}
                />
                <Button
                  onClick={async () => {
                    if (!analyticsQuery.trim()) {
                      setAnalyticsRows([]);
                      appToast.error('Enter a user name or email to search.');
                      return;
                    }
                    const res = (await searchAnalyticsUser(analyticsQuery)) as {
                      data?: Record<string, unknown>[];
                    };
                    setAnalyticsRows(res.data ?? []);
                  }}
                >
                  Search
                </Button>
              </div>
              <pre className="max-h-[320px] overflow-auto rounded-md border p-3 text-xs scroll-premium">
                {JSON.stringify(analyticsRows, null, 2)}
              </pre>
              {analyticsRows.length > 0 && (
                <div className="grid gap-3 md:grid-cols-2">
                  {analyticsRows.map((r, idx) => (
                    <Card key={`${String(r.user_id ?? idx)}`}>
                      <CardContent className="pt-4 text-xs space-y-1">
                        <p className="font-medium">{String(r.name ?? '—')} · {String(r.email ?? '—')}</p>
                        <p className="text-muted-foreground">
                          Uploads: {Number(r.uploads ?? 0)} · Tenders: {Number(r.tenders ?? 0)} · Proposals: {Number(r.proposals ?? 0)}
                        </p>
                        <p className="text-muted-foreground">
                          Payments: {Number(r.payments ?? 0)} · Activity: {Number(r.activity ?? 0)}
                        </p>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}

      </div>
    </AdminRouteGuard>
  );
}
