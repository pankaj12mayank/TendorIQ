'use client';

import Link from 'next/link';
import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  AlertTriangle,
  BarChart3,
  CreditCard,
  FileText,
  History,
  Loader2,
  Rocket,
  Search,
  Trash2,
  Upload,
  Wand2,
} from 'lucide-react';

import { AdminRouteGuard } from '@/components/auth/admin-route-guard';
import { DashboardIntelligence } from '@/components/dashboard/dashboard-intelligence';
import { PageHeader, Breadcrumbs } from '@/components/design-system/page-header';
import { KpiCard } from '@/components/design-system/kpi-card';
import {
  DataTableShell,
  DataTable,
  DataTableHeader,
  DataTableHead,
  DataTableBody,
  DataTableRow,
  DataTableCell,
} from '@/components/design-system/data-table';
import { StatusBadge } from '@/components/design-system/status-badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useCurrentUser } from '@/hooks/use-auth';
import { useDeleteTender, useTenders } from '@/hooks/use-api';
import { TableRowSkeleton } from '@/components/design-system/skeleton';
import { PremiumErrorState } from '@/components/design-system/empty-state';
import { ROUTES } from '@/lib/routes';
import { isSuperAdmin } from '@/lib/permissions';
import { api } from '@/lib/api-client';
import { mapQuotaFromUsageApi } from '@/lib/billing-api';
import { unwrapData } from '@/lib/api-envelope';
import { appToast } from '@/lib/app-toast';

export default function DashboardPage() {
  const user = useCurrentUser();
  const isOwner = isSuperAdmin(user?.role);
  if (isOwner) {
    return (
      <AdminRouteGuard>
        <DashboardIntelligence />
      </AdminRouteGuard>
    );
  }
  return <MemberDashboard />;
}

function MemberDashboard() {
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [search, setSearch] = useState('');
  const [deletingTenderId, setDeletingTenderId] = useState<string | null>(null);
  const limit = 8;
  const tenderQueryParams = {
    limit,
    page,
    ...(statusFilter !== 'all' ? { status: statusFilter } : {}),
    ...(search.trim() ? { search: search.trim() } : {}),
  } as Record<string, string | number>;
  const { data, isLoading, isError, refetch } = useTenders(tenderQueryParams);
  const deleteTender = useDeleteTender();
  const tenders = data?.data ?? [];
  const totalPages = Number(data?.meta?.totalPages ?? 0);
  const subscriptionQuery = useQuery({
    queryKey: ['member-dashboard', 'subscription'],
    queryFn: async () =>
      unwrapData(await api.get('/api/v1/billing/subscription')) as Record<string, any>,
  });
  const quotaQuery = useQuery({
    queryKey: ['member-dashboard', 'quota'],
    queryFn: async () => mapQuotaFromUsageApi(await api.get('/api/v1/billing/quota')),
  });
  const recentUploadsQuery = useQuery({
    queryKey: ['member-dashboard', 'recent-uploads'],
    queryFn: async () => {
      const res = await api.get<Record<string, any>>('/api/v1/files/list', {
        params: { page: 1, limit: 5 },
      });
      return Array.isArray(res.files) ? res.files : [];
    },
  });
  const recentAnalysesQuery = useQuery({
    queryKey: ['member-dashboard', 'recent-analyses'],
    queryFn: async () => {
      const res = await api.get('/api/v1/analysis', { params: { page: 1, limit: 5 } });
      const body = unwrapData<any[]>(res as any);
      return Array.isArray(body) ? body : [];
    },
  });
  const subscription = subscriptionQuery.data ?? {};
  const quota = quotaQuery.data ?? [];
  const currentPlan = String(subscription.plan ?? 'pro').toUpperCase();
  const currentPeriodEnd =
    subscription.currentPeriodEnd ?? subscription.current_period_end ?? subscription.expiry ?? null;
  const expiryDate = currentPeriodEnd ? new Date(currentPeriodEnd) : null;
  const now = new Date();
  const isExpired = !!expiryDate && expiryDate.getTime() <= now.getTime();
  const daysToExpiry = expiryDate
    ? Math.ceil((expiryDate.getTime() - now.getTime()) / 86400000)
    : null;
  const usageQuota = useMemo(() => {
    const item = quota.find((q: any) => {
      const key = String(q.featureKey ?? q.resource ?? q.feature_name ?? '').toLowerCase();
      return key.includes('upload') || key.includes('document');
    }) as Record<string, any> | undefined;
    if (!item) return { used: 0, limit: 0, remaining: null as number | null };
    const used = Number(item.used ?? item.current ?? 0);
    const limitVal = Number(item.limit ?? item.max ?? 0);
    const remainingRaw = item.remaining;
    const remaining =
      typeof remainingRaw === 'number'
        ? remainingRaw
        : limitVal > 0
          ? Math.max(limitVal - used, 0)
          : null;
    return { used, limit: limitVal, remaining };
  }, [quota]);
  const showNearLimitBanner =
    !isExpired &&
    typeof usageQuota.remaining === 'number' &&
    usageQuota.remaining >= 0 &&
    usageQuota.remaining <= 3;

  async function handleDeleteTender(tenderId: string) {
    if (!confirm('Delete this tender? This action cannot be undone.')) return;
    setDeletingTenderId(tenderId);
    try {
      await deleteTender.mutateAsync(tenderId);
      appToast.success('Tender deleted');
      await refetch();
    } catch (error) {
      appToast.error(error instanceof Error ? error.message : 'Failed to delete tender');
    } finally {
      setDeletingTenderId(null);
    }
  }

  return (
    <div className="space-y-8 app-page">
      <PageHeader
        title="Dashboard"
        description="Track plan, usage, and value from your paid workspace."
        breadcrumbs={
          <Breadcrumbs items={[{ label: 'Home', href: '/dashboard' }, { label: 'Dashboard' }]} />
        }
        actions={
          <Button asChild>
            <Link href={ROUTES.upload}>
              <Upload className="h-4 w-4" />
              Upload tender
            </Link>
          </Button>
        }
      />
      {isExpired ? (
        <Card className="border-destructive/50 bg-destructive/5">
          <CardContent className="flex items-center gap-3 py-4">
            <AlertTriangle className="h-4 w-4 text-destructive" />
            <p className="text-sm font-medium">Your plan expired. Please renew to continue.</p>
          </CardContent>
        </Card>
      ) : null}
      {showNearLimitBanner ? (
        <Card className="border-amber-500/40 bg-amber-500/5">
          <CardContent className="flex items-center gap-3 py-4">
            <AlertTriangle className="h-4 w-4 text-amber-500" />
            <p className="text-sm font-medium">
              You have {usageQuota.remaining} uploads remaining
            </p>
          </CardContent>
        </Card>
      ) : null}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          title="Current plan"
          value={currentPlan}
          trend={subscriptionQuery.isLoading ? '...' : String(subscription.status ?? 'active')}
          icon={FileText}
        />
        <KpiCard
          title="Plan expiry"
          value={daysToExpiry == null ? '—' : `Expires in ${Math.max(daysToExpiry, 0)} days`}
          trend={expiryDate ? expiryDate.toLocaleDateString() : ''}
          trendUp={!isExpired}
          icon={History}
        />
        <KpiCard
          title="Usage"
          value={
            usageQuota.limit > 0
              ? `${usageQuota.used}/${usageQuota.limit} uploads used`
              : `${usageQuota.used} uploads used`
          }
          trend={typeof usageQuota.remaining === 'number' ? `${usageQuota.remaining} remaining` : ''}
          trendUp
          icon={BarChart3}
        />
        <KpiCard
          title="Recent analyses"
          value={String(recentAnalysesQuery.data?.length ?? 0)}
          trend={recentAnalysesQuery.isLoading ? '...' : 'latest 5'}
          icon={Rocket}
        />
      </div>
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Quick actions</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
          <Button asChild variant="default">
            <Link href={ROUTES.upload}>
              <Upload className="h-4 w-4" />
              Upload Tender
            </Link>
          </Button>
          <Button asChild variant="outline">
            <Link href={ROUTES.analysis}>
              <Search className="h-4 w-4" />
              View Analysis
            </Link>
          </Button>
          <Button asChild variant="outline">
            <Link href={ROUTES.proposal}>
              <Wand2 className="h-4 w-4" />
              Generate Proposal
            </Link>
          </Button>
          <Button asChild variant="outline">
            <Link href={ROUTES.billing}>
              <CreditCard className="h-4 w-4" />
              Payment History
            </Link>
          </Button>
        </CardContent>
      </Card>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Recent uploads</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {recentUploadsQuery.isLoading ? (
              <p className="text-sm text-muted-foreground">Loading uploads...</p>
            ) : (recentUploadsQuery.data ?? []).length === 0 ? (
              <p className="text-sm text-muted-foreground">No uploads yet. Upload a tender to get started.</p>
            ) : (
              (recentUploadsQuery.data ?? []).slice(0, 5).map((row: any) => (
                <div
                  key={String(row.id)}
                  className="flex items-center justify-between rounded-md border p-2 text-sm"
                >
                  <span className="truncate pr-3">{row.file_name || row.name}</span>
                  <StatusBadge status={String(row.status || 'processing') as any} />
                </div>
              ))
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Recent analyses</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {recentAnalysesQuery.isLoading ? (
              <p className="text-sm text-muted-foreground">Loading analyses...</p>
            ) : (recentAnalysesQuery.data ?? []).length === 0 ? (
              <p className="text-sm text-muted-foreground">No analyses yet. Upload a tender first.</p>
            ) : (
              (recentAnalysesQuery.data ?? []).slice(0, 5).map((row: any) => (
                <div
                  key={String(row.id)}
                  className="flex items-center justify-between rounded-md border p-2 text-sm"
                >
                  <span className="truncate pr-3">{String(row.analysis_type || 'analysis')}</span>
                  <span className="text-muted-foreground">
                    {row.created_at ? new Date(row.created_at).toLocaleDateString() : '—'}
                  </span>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
      <DataTableShell
        title="Recent tenders"
        description="Only your tenders are shown."
        toolbar={
          <div className="flex w-full flex-col gap-2 sm:flex-row sm:items-center sm:justify-end">
            <Input
              value={search}
              onChange={(e) => {
                setPage(1);
                setSearch(e.target.value);
              }}
              placeholder="Search tenders"
              className="sm:w-56"
            />
            <Select
              value={statusFilter}
              onValueChange={(value) => {
                setPage(1);
                setStatusFilter(value);
              }}
            >
              <SelectTrigger className="sm:w-44">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All statuses</SelectItem>
                <SelectItem value="draft">Draft</SelectItem>
                <SelectItem value="published">Published</SelectItem>
                <SelectItem value="closed">Closed</SelectItem>
                <SelectItem value="awarded">Awarded</SelectItem>
                <SelectItem value="cancelled">Cancelled</SelectItem>
              </SelectContent>
            </Select>
          </div>
        }
      >
        {isLoading ? (
          <DataTable>
            <DataTableHeader>
              <tr>
                <DataTableHead>Title</DataTableHead>
                <DataTableHead>Status</DataTableHead>
                <DataTableHead>Created</DataTableHead>
                <DataTableHead className="text-right">Actions</DataTableHead>
              </tr>
            </DataTableHeader>
            <DataTableBody>
              {Array.from({ length: 5 }).map((_, i) => (
                <TableRowSkeleton key={i} cols={4} />
              ))}
            </DataTableBody>
          </DataTable>
        ) : isError ? (
          <div className="p-4">
            <PremiumErrorState onRetry={() => refetch()} />
          </div>
        ) : (
          <DataTable>
            <DataTableHeader>
              <tr>
                <DataTableHead>Title</DataTableHead>
                <DataTableHead>Status</DataTableHead>
                <DataTableHead>Created</DataTableHead>
                <DataTableHead className="text-right">Actions</DataTableHead>
              </tr>
            </DataTableHeader>
            <DataTableBody>
              {tenders.map((tender) => (
                <DataTableRow key={tender.id}>
                  <DataTableCell className="font-medium">{tender.title}</DataTableCell>
                  <DataTableCell>
                    <StatusBadge
                      status={
                        tender.status === 'published'
                          ? 'published'
                          : tender.status === 'draft'
                            ? 'draft'
                            : 'processing'
                      }
                    />
                  </DataTableCell>
                  <DataTableCell className="text-muted-foreground">
                    {new Date(tender.createdAt).toLocaleDateString()}
                  </DataTableCell>
                  <DataTableCell className="text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => void handleDeleteTender(tender.id)}
                      disabled={deletingTenderId === tender.id}
                    >
                      {deletingTenderId === tender.id ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Trash2 className="h-4 w-4" />
                      )}
                    </Button>
                  </DataTableCell>
                </DataTableRow>
              ))}
              {!tenders.length ? (
                <DataTableRow>
                  <DataTableCell colSpan={4} className="text-center text-sm text-muted-foreground">
                    No tenders found for current filters.
                  </DataTableCell>
                </DataTableRow>
              ) : null}
            </DataTableBody>
          </DataTable>
        )}
        <div className="mt-4 flex items-center justify-between">
          <p className="text-xs text-muted-foreground">
            Page {Number(data?.meta?.page ?? page)} of {Math.max(totalPages, 1)}
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Prev
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={totalPages > 0 ? page >= totalPages : tenders.length < limit}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      </DataTableShell>
    </div>
  );
}
