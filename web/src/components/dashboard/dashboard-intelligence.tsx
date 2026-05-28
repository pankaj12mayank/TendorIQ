'use client';

import Link from 'next/link';
import { useMemo, useState } from 'react';
import {
  CloudUpload,
  FileText,
  Trash2,
  TrendingUp,
  Users,
  DollarSign,
  AlertTriangle,
} from 'lucide-react';

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
import { PremiumErrorState } from '@/components/design-system/empty-state';
import { TableRowSkeleton } from '@/components/design-system/skeleton';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '@/components/ui/pagination';
import { appToast } from '@/lib/app-toast';
import {
  useDashboardOverview,
  useDashboardRegisteredUsers,
  useDashboardTenders,
  useDashboardUserOptions,
  useDeleteDashboardTender,
} from '@/hooks/use-dashboard-intelligence';
import type { StatusType } from '@/design-system/tokens';

function tenderStatusBadge(status: string): StatusType {
  if (status === 'published') return 'published';
  if (status === 'draft') return 'draft';
  if (status === 'closed' || status === 'cancelled') return 'archived';
  return 'processing';
}

function DashboardQuickActions() {
  return (
    <div className="flex flex-wrap items-center justify-end gap-2">
      <Button variant="outline" size="sm" asChild>
        <Link href="/dashboard/analysis">
          <FileText className="h-4 w-4" />
          Analysis
        </Link>
      </Button>
      <Button variant="outline" size="sm" asChild>
        <Link href="/dashboard/proposal">
          <TrendingUp className="h-4 w-4" />
          Proposals
        </Link>
      </Button>
      <Button size="sm" asChild>
        <Link href="/dashboard/upload">
          <CloudUpload className="h-4 w-4" />
          Upload
        </Link>
      </Button>
    </div>
  );
}

export function DashboardIntelligence() {
  const [tenderPage, setTenderPage] = useState(1);
  const [tenderStatus, setTenderStatus] = useState<string>('all');
  const [tenderUserId, setTenderUserId] = useState<string>('all');
  const [userFilterSearch, setUserFilterSearch] = useState('');
  const [tenderSearch, setTenderSearch] = useState('');
  const [userStatus, setUserStatus] = useState<string>('all');
  const [userPlan, setUserPlan] = useState<string>('all');
  const [overviewListTab, setOverviewListTab] = useState<'tenders' | 'users'>('tenders');

  const overview = useDashboardOverview();
  const userOptions = useDashboardUserOptions(userFilterSearch || undefined);
  const tenders = useDashboardTenders({
    page: tenderPage,
    limit: 10,
    status: tenderStatus === 'all' ? undefined : tenderStatus,
    user_id: tenderUserId === 'all' ? undefined : tenderUserId,
    search: tenderSearch || undefined,
  });
  const registered = useDashboardRegisteredUsers({
    page: 1,
    limit: 8,
    status: userStatus === 'all' ? undefined : userStatus,
    plan: userPlan === 'all' ? undefined : userPlan,
  });
  const deleteTender = useDeleteDashboardTender();

  const planOptions = useMemo(() => {
    const plans = Object.keys(registered.data?.summary.by_plan ?? {});
    return plans.length ? plans : ['free'];
  }, [registered.data?.summary.by_plan]);

  const formatMoney = (amount: number, currency = 'USD') =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency, maximumFractionDigits: 0 }).format(
      amount
    );

  return (
    <div className="space-y-5 app-page">
      <div className="flex items-center justify-end">
        <DashboardQuickActions />
      </div>

      {/* Admin overview */}
      {overview.isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-28 rounded-xl bg-muted/40 animate-pulse" />
          ))}
        </div>
      ) : overview.isError ? (
        <PremiumErrorState onRetry={() => void overview.refetch()} />
      ) : overview.data ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <KpiCard
              title="Uploads today"
              value={String(overview.data.uploads_today)}
              icon={CloudUpload}
            />
            <KpiCard
              title="Active users"
              value={String(overview.data.active_users)}
              trend={`${overview.data.inactive_users} inactive`}
              icon={Users}
            />
            <KpiCard
              title="Revenue"
              value={formatMoney(overview.data.revenue)}
              icon={DollarSign}
            />
            <KpiCard
              title="Failed AI jobs"
              value={String(overview.data.failed_ai_jobs)}
              trendUp={overview.data.failed_ai_jobs === 0}
              trend={overview.data.failed_ai_jobs === 0 ? 'None' : 'Needs attention'}
              icon={AlertTriangle}
            />
          </div>

          {overview.data.recent_payments.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">Recent payments</CardTitle>
                <CardDescription>Latest transactions across the platform</CardDescription>
              </CardHeader>
              <CardContent className="table-wrap">
                <DataTable>
                  <DataTableHeader>
                    <tr>
                      <DataTableHead>User</DataTableHead>
                      <DataTableHead>Plan</DataTableHead>
                      <DataTableHead>Amount</DataTableHead>
                      <DataTableHead>Status</DataTableHead>
                      <DataTableHead>Date</DataTableHead>
                    </tr>
                  </DataTableHeader>
                  <DataTableBody>
                    {overview.data.recent_payments.map((p) => (
                      <DataTableRow key={p.id}>
                        <DataTableCell className="text-sm">{p.user_email}</DataTableCell>
                        <DataTableCell className="text-sm text-muted-foreground">
                          {p.plan ?? '—'}
                        </DataTableCell>
                        <DataTableCell className="text-sm tabular-nums">
                          {formatMoney(p.amount, p.currency || 'USD')}
                        </DataTableCell>
                        <DataTableCell>
                          <StatusBadge
                            status={p.status === 'paid' ? 'completed' : p.status === 'failed' ? 'failed' : 'processing'}
                            label={p.status}
                          />
                        </DataTableCell>
                        <DataTableCell className="text-sm text-muted-foreground">
                          {p.created_at ? new Date(p.created_at).toLocaleString() : '—'}
                        </DataTableCell>
                      </DataTableRow>
                    ))}
                  </DataTableBody>
                </DataTable>
              </CardContent>
            </Card>
          )}
        </>
      ) : null}

      <div className="space-y-4">
        <div className="flex flex-wrap gap-2">
          <Button
            size="sm"
            variant={overviewListTab === 'tenders' ? 'default' : 'outline'}
            onClick={() => setOverviewListTab('tenders')}
          >
            Recent tenders
          </Button>
          <Button
            size="sm"
            variant={overviewListTab === 'users' ? 'default' : 'outline'}
            onClick={() => setOverviewListTab('users')}
          >
            Registered users
          </Button>
        </div>
        {overviewListTab === 'tenders' && (
          <DataTableShell
            title="Recent tenders"
            description="Paginated workspace tenders with filters"
            toolbar={
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                <Input
                  placeholder="Search title…"
                  value={tenderSearch}
                  onChange={(e) => {
                    setTenderSearch(e.target.value);
                    setTenderPage(1);
                  }}
                  className="h-9 w-full sm:w-40"
                />
                <Select
                  value={tenderStatus}
                  onValueChange={(v) => {
                    setTenderStatus(v);
                    setTenderPage(1);
                  }}
                >
                  <SelectTrigger className="h-9 w-full sm:w-32">
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All statuses</SelectItem>
                    <SelectItem value="draft">Draft</SelectItem>
                    <SelectItem value="published">Published</SelectItem>
                    <SelectItem value="closed">Closed</SelectItem>
                    <SelectItem value="cancelled">Cancelled</SelectItem>
                  </SelectContent>
                </Select>
                <Select
                  value={tenderUserId}
                  onValueChange={(v) => {
                    setTenderUserId(v);
                    setTenderPage(1);
                  }}
                >
                  <SelectTrigger className="h-9 w-full sm:w-44">
                    <SelectValue placeholder="User" />
                  </SelectTrigger>
                  <SelectContent>
                    <div className="px-2 pb-2">
                      <Input
                        value={userFilterSearch}
                        onChange={(e) => setUserFilterSearch(e.target.value)}
                        placeholder="Search user…"
                        className="h-8"
                      />
                    </div>
                    <SelectItem value="all">All users</SelectItem>
                    {(userOptions.data ?? []).map((u) => (
                      <SelectItem key={u.id} value={u.id}>
                        {u.email}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            }
          >
            {tenders.isLoading ? (
              <DataTable>
                <DataTableHeader>
                  <tr>
                    <DataTableHead>Title</DataTableHead>
                    <DataTableHead>Owner</DataTableHead>
                    <DataTableHead>Status</DataTableHead>
                    <DataTableHead />
                  </tr>
                </DataTableHeader>
                <DataTableBody>
                  {Array.from({ length: 5 }).map((_, i) => (
                    <TableRowSkeleton key={i} cols={4} />
                  ))}
                </DataTableBody>
              </DataTable>
            ) : tenders.isError ? (
              <div className="p-4">
                <PremiumErrorState onRetry={() => void tenders.refetch()} />
              </div>
            ) : (
              <>
                <DataTable>
                  <DataTableHeader>
                    <tr>
                      <DataTableHead>Title</DataTableHead>
                      <DataTableHead>Owner</DataTableHead>
                      <DataTableHead>Status</DataTableHead>
                      <DataTableHead className="w-24">Actions</DataTableHead>
                    </tr>
                  </DataTableHeader>
                  <DataTableBody>
                    {(tenders.data?.items ?? []).map((tender) => (
                      <DataTableRow key={tender.id}>
                        <DataTableCell className="font-medium max-w-[200px] truncate">
                          {tender.title}
                        </DataTableCell>
                        <DataTableCell className="text-sm text-muted-foreground">
                          {tender.owner_email}
                        </DataTableCell>
                        <DataTableCell>
                          <StatusBadge status={tenderStatusBadge(tender.status)} />
                        </DataTableCell>
                        <DataTableCell>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-destructive hover:text-destructive"
                            aria-label={`Delete ${tender.title}`}
                            disabled={deleteTender.isPending}
                            onClick={() => {
                              if (!window.confirm(`Delete tender "${tender.title}"?`)) return;
                              deleteTender.mutate(tender.id, {
                                onSuccess: () => appToast.success('Tender deleted.'),
                                onError: () => appToast.error('Could not delete tender.'),
                              });
                            }}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </DataTableCell>
                      </DataTableRow>
                    ))}
                  </DataTableBody>
                </DataTable>
                {(tenders.data?.pagination.pages ?? 0) > 1 && (
                  <Pagination className="mt-4 justify-start sm:justify-end">
                    <PaginationContent>
                      <PaginationItem>
                        <PaginationPrevious
                          disabled={tenderPage <= 1}
                          onClick={() => setTenderPage((p) => Math.max(1, p - 1))}
                        />
                      </PaginationItem>
                      <PaginationItem>
                        <PaginationLink isActive>
                          {tenderPage} / {tenders.data?.pagination.pages ?? 1}
                        </PaginationLink>
                      </PaginationItem>
                      <PaginationItem>
                        <PaginationNext
                          disabled={tenderPage >= (tenders.data?.pagination.pages ?? 1)}
                          onClick={() => setTenderPage((p) => p + 1)}
                        />
                      </PaginationItem>
                    </PaginationContent>
                  </Pagination>
                )}
              </>
            )}
          </DataTableShell>
        )}
        {overviewListTab === 'users' && (
          <Card>
            <CardHeader className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <CardTitle className="text-base flex items-center gap-2">
                  <Users className="h-4 w-4" />
                  Registered users
                </CardTitle>
                <CardDescription>Excludes platform owner account</CardDescription>
              </div>
              <div className="flex flex-wrap gap-2">
                <Select value={userStatus} onValueChange={setUserStatus}>
                  <SelectTrigger className="h-9 w-32">
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All</SelectItem>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="inactive">Inactive</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={userPlan} onValueChange={setUserPlan}>
                  <SelectTrigger className="h-9 w-28">
                    <SelectValue placeholder="Plan" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All plans</SelectItem>
                    {planOptions.map((p) => (
                      <SelectItem key={p} value={p}>
                        {p}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {registered.isLoading ? (
                <div className="h-24 rounded-lg bg-muted/40 animate-pulse" />
              ) : registered.data ? (
                <>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
                    <div className="rounded-md border p-3">
                      <p className="text-muted-foreground">Active</p>
                      <p className="text-xl font-semibold tabular-nums">
                        {registered.data.summary.active_users}
                      </p>
                    </div>
                    <div className="rounded-md border p-3">
                      <p className="text-muted-foreground">Inactive</p>
                      <p className="text-xl font-semibold tabular-nums">
                        {registered.data.summary.inactive_users}
                      </p>
                    </div>
                    {Object.entries(registered.data.summary.by_plan).map(([plan, count]) => (
                      <div key={plan} className="rounded-md border p-3">
                        <p className="text-muted-foreground capitalize">{plan}</p>
                        <p className="text-xl font-semibold tabular-nums">{count}</p>
                      </div>
                    ))}
                  </div>
                  <div className="table-wrap">
                    <DataTable>
                      <DataTableHeader>
                        <tr>
                          <DataTableHead>User</DataTableHead>
                          <DataTableHead>Plan</DataTableHead>
                          <DataTableHead>Usage</DataTableHead>
                          <DataTableHead>Status</DataTableHead>
                        </tr>
                      </DataTableHeader>
                      <DataTableBody>
                        {registered.data.users.map((u) => (
                          <DataTableRow key={u.id}>
                            <DataTableCell>
                              <p className="text-sm font-medium">{u.name}</p>
                              <p className="text-xs text-muted-foreground">{u.email}</p>
                            </DataTableCell>
                            <DataTableCell className="text-sm capitalize">{u.plan}</DataTableCell>
                            <DataTableCell className="text-xs text-muted-foreground">
                              {u.usage.uploads} uploads · {u.usage.analysis} analysis ·{' '}
                              {u.usage.proposals} proposals
                            </DataTableCell>
                            <DataTableCell>
                              <StatusBadge
                                status={u.status === 'active' ? 'completed' : 'draft'}
                                label={u.status}
                              />
                            </DataTableCell>
                          </DataTableRow>
                        ))}
                      </DataTableBody>
                    </DataTable>
                  </div>
                </>
              ) : null}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
