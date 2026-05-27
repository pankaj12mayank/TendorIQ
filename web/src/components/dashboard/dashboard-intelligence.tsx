'use client';

import Link from 'next/link';
import { useMemo, useState } from 'react';
import {
  ArrowRight,
  CloudUpload,
  FileText,
  Loader2,
  RefreshCw,
  Trash2,
  TrendingUp,
  Users,
  DollarSign,
  AlertTriangle,
  Sparkles,
} from 'lucide-react';

import { PageHeader, Breadcrumbs } from '@/components/design-system/page-header';
import { KpiCard } from '@/components/design-system/kpi-card';
import { AiProcessingPipeline } from '@/components/design-system/ai-pipeline';
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
import { ROUTES } from '@/lib/routes';
import { appToast } from '@/lib/app-toast';
import {
  useDashboardOverview,
  useDashboardPipeline,
  useDashboardRegisteredUsers,
  useDashboardTenders,
  useDashboardUserOptions,
  useDeleteDashboardTender,
  type PipelineJob,
} from '@/hooks/use-dashboard-intelligence';
import type { StatusType } from '@/design-system/tokens';

function tenderStatusBadge(status: string): StatusType {
  if (status === 'published') return 'published';
  if (status === 'draft') return 'draft';
  if (status === 'closed' || status === 'cancelled') return 'archived';
  return 'processing';
}

function docStatusBadge(status: string): StatusType {
  const map: Record<string, StatusType> = {
    uploaded: 'uploaded',
    processing: 'processing',
    retrying: 'retrying',
    completed: 'completed',
    failed: 'failed',
    needs_review: 'needs_review',
  };
  return map[status] ?? 'processing';
}

function DashboardQuickActions() {
  return (
    <div className="flex flex-wrap items-center justify-end gap-2">
      <Button variant="outline" size="sm" asChild>
        <Link href={ROUTES.analysis}>
          <FileText className="h-4 w-4" />
          Analysis
        </Link>
      </Button>
      <Button variant="outline" size="sm" asChild>
        <Link href={ROUTES.proposal}>
          <TrendingUp className="h-4 w-4" />
          Proposals
        </Link>
      </Button>
      <Button size="sm" asChild>
        <Link href={ROUTES.upload}>
          <CloudUpload className="h-4 w-4" />
          Upload
        </Link>
      </Button>
    </div>
  );
}

function PipelineJobCard({ job }: { job: PipelineJob }) {
  const p = job.pipeline;
  return (
    <div className="rounded-lg border border-border/60 p-4 space-y-3">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-sm font-medium truncate">{job.document_name}</p>
          <p className="text-xs text-muted-foreground truncate">
            {job.owner_email}
            {job.tender_title ? ` · ${job.tender_title}` : ''}
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {p.is_retrying && (
            <StatusBadge status="retrying" label={`Retry ${p.retry_count}`} />
          )}
          <StatusBadge status={docStatusBadge(job.processing_status)} />
        </div>
      </div>
      <AiProcessingPipeline
        title=""
        steps={p.stages}
        animated={false}
        className="!p-0 !bg-transparent border-0 shadow-none"
      />
      {p.is_failed && job.pipeline.stages.find((s) => s.status === 'failed')?.description && (
        <p className="text-xs text-destructive">
          {job.pipeline.stages.find((s) => s.status === 'failed')?.description}
        </p>
      )}
    </div>
  );
}

export function DashboardIntelligence() {
  const [tenderPage, setTenderPage] = useState(1);
  const [pipelinePage, setPipelinePage] = useState(1);
  const [tenderStatus, setTenderStatus] = useState<string>('all');
  const [tenderUserId, setTenderUserId] = useState<string>('all');
  const [userFilterSearch, setUserFilterSearch] = useState('');
  const [tenderSearch, setTenderSearch] = useState('');
  const [userStatus, setUserStatus] = useState<string>('all');
  const [userPlan, setUserPlan] = useState<string>('all');
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);

  const overview = useDashboardOverview();
  const pipeline = useDashboardPipeline({ page: pipelinePage, limit: 8 });
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

  const jobs = pipeline.data?.jobs ?? [];
  const activeJob =
    jobs.find((j) => j.document_id === selectedJobId) ??
    jobs.find((j) => !j.pipeline.is_terminal) ??
    jobs[0];

  const planOptions = useMemo(() => {
    const plans = Object.keys(registered.data?.summary.by_plan ?? {});
    return plans.length ? plans : ['free'];
  }, [registered.data?.summary.by_plan]);

  const formatMoney = (amount: number, currency = 'INR') =>
    new Intl.NumberFormat('en-IN', { style: 'currency', currency, maximumFractionDigits: 0 }).format(
      amount
    );

  return (
    <div className="space-y-8 app-page">
      <PageHeader
        title="Operations"
        description="Live pipeline state, users, and platform metrics from the database."
        breadcrumbs={
          <Breadcrumbs
            items={[
              { label: 'Home', href: ROUTES.dashboard },
              { label: 'Operations' },
            ]}
          />
        }
        actions={<DashboardQuickActions />}
      />

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
                          {formatMoney(p.amount, p.currency || 'INR')}
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

      <div className="grid gap-6 lg:grid-cols-5">
        <div className="lg:col-span-3 space-y-6">
          {/* Recent tenders */}
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

          {/* Registered users */}
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
        </div>

        {/* Live AI pipeline */}
        <div className="lg:col-span-2 space-y-4">
          <div className="surface-card p-5">
            <div className="flex items-center justify-between gap-2 mb-4">
              <div className="flex items-center gap-2 text-primary">
                <Sparkles className="h-4 w-4" />
                <span className="text-sm font-semibold">Live AI pipeline</span>
              </div>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                aria-label="Refresh pipeline"
                onClick={() => void pipeline.refetch()}
                disabled={pipeline.isFetching}
              >
                {pipeline.isFetching ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4" />
                )}
              </Button>
            </div>
            {pipeline.isLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 2 }).map((_, i) => (
                  <div key={i} className="h-32 rounded-lg bg-muted/40 animate-pulse" />
                ))}
              </div>
            ) : pipeline.isError ? (
              <PremiumErrorState onRetry={() => void pipeline.refetch()} />
            ) : jobs.length === 0 ? (
              <p className="text-sm text-muted-foreground">No recent AI jobs.</p>
            ) : (
              <div className="space-y-4">
                {activeJob && <PipelineJobCard job={activeJob} />}
                {jobs.length > 1 && (
                  <div className="space-y-1 border-t pt-3">
                    <p className="text-xs font-medium text-muted-foreground mb-2">All jobs</p>
                    {jobs.map((job) => (
                      <button
                        key={job.document_id}
                        type="button"
                        onClick={() => setSelectedJobId(job.document_id)}
                        className={`w-full flex items-center justify-between rounded-md px-2 py-2 text-left text-sm hover:bg-muted/60 ${
                          activeJob?.document_id === job.document_id ? 'bg-muted/80' : ''
                        }`}
                      >
                        <span className="truncate flex-1">{job.document_name}</span>
                        <StatusBadge status={docStatusBadge(job.processing_status)} showIcon={false} />
                      </button>
                    ))}
                  </div>
                )}
                {pipeline.data?.has_active && (
                  <p className="text-xs text-muted-foreground flex items-center gap-1">
                    <Loader2 className="h-3 w-3 animate-spin" />
                    Syncing every 8s while jobs are active
                  </p>
                )}
                {(pipeline.data?.pagination.pages ?? 0) > 1 && (
                  <Pagination className="justify-start">
                    <PaginationContent>
                      <PaginationItem>
                        <PaginationPrevious
                          disabled={pipelinePage <= 1}
                          onClick={() => setPipelinePage((p) => Math.max(1, p - 1))}
                        />
                      </PaginationItem>
                      <PaginationItem>
                        <PaginationLink isActive>
                          {pipelinePage} / {pipeline.data?.pagination.pages ?? 1}
                        </PaginationLink>
                      </PaginationItem>
                      <PaginationItem>
                        <PaginationNext
                          disabled={pipelinePage >= (pipeline.data?.pagination.pages ?? 1)}
                          onClick={() => setPipelinePage((p) => p + 1)}
                        />
                      </PaginationItem>
                    </PaginationContent>
                  </Pagination>
                )}
              </div>
            )}
          </div>

          <div className="surface-card p-5">
            <div className="flex items-center gap-2 text-primary mb-3">
              <ArrowRight className="h-4 w-4" />
              <span className="text-sm font-semibold">Platform</span>
            </div>
            <Button variant="outline" size="sm" className="w-full" asChild>
              <Link href={ROUTES.admin}>Full admin console</Link>
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
