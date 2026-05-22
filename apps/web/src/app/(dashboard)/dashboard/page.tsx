'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import {
  FileText,
  Users,
  TrendingUp,
  DollarSign,
  ArrowRight,
  Sparkles,
  Upload,
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
import { CanCreateTender } from '@/components/auth/rbac';
import { Button } from '@/components/ui/button';
import { useTenders } from '@/hooks/use-api';
import { LoadingState } from '@/components/ui/loading-state';
import { PremiumErrorState } from '@/components/design-system/empty-state';
import { staggerContainer } from '@/design-system/motion';

const pipelineSteps = [
  { id: '1', label: 'Document upload', status: 'completed' as const },
  { id: '2', label: 'OCR extraction', status: 'completed' as const },
  { id: '3', label: 'AI analysis', status: 'active' as const, description: 'Extracting requirements...' },
  { id: '4', label: 'Risk scoring', status: 'pending' as const },
  { id: '5', label: 'Checklist generation', status: 'pending' as const },
];

export default function DashboardPage() {
  const { data, isLoading, isError, refetch } = useTenders({ limit: 8 });
  const tenders = data?.data ?? [];
  const activeTenders = tenders.filter(t => t.status === 'published').length;
  const pipelineValue = tenders.reduce((sum, t) => sum + (Number(t.budget) || 0), 0);
  const organizationCount = new Set(tenders.map(t => t.organizationId).filter(Boolean)).size;

  return (
    <div className="space-y-8">
      <PageHeader
        title="Procurement command center"
        description="Monitor tenders, AI pipelines, and team activity in one operational view."
        breadcrumbs={
          <Breadcrumbs items={[{ label: 'Home', href: '/dashboard' }, { label: 'Dashboard' }]} />
        }
        actions={
          <Button asChild>
            <Link href="/dashboard/upload">
              <Upload className="h-4 w-4" />
              Upload tender
            </Link>
          </Button>
        }
      />

      <motion.div
        variants={staggerContainer}
        initial="initial"
        animate="animate"
        className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"
      >
        <KpiCard title="Active tenders" value={String(activeTenders)} trend={isLoading ? '...' : `${activeTenders > 0 ? '+' : ''}${activeTenders}`} trendUp icon={FileText} delay={0} />
        <KpiCard title="Organizations" value={String(organizationCount || '—')} trend="0%" icon={Users} delay={0.05} />
        <KpiCard title="Pipeline value" value={pipelineValue > 0 ? `$${(pipelineValue / 1000).toFixed(0)}K` : '—'} trend={isLoading ? '...' : '+'} trendUp icon={DollarSign} delay={0.1} />
        <KpiCard title="Total tenders" value={String(tenders.length)} trend={isLoading ? '...' : ''} icon={TrendingUp} delay={0.15} />
      </motion.div>

      <div className="grid gap-6 lg:grid-cols-5">
        <div className="lg:col-span-3">
          <DataTableShell
            title="Recent tenders"
            description="Latest procurement activity across your workspace"
            toolbar={
              <Button variant="outline" size="sm" asChild>
                <Link href="/dashboard/tenders">View all</Link>
              </Button>
            }
          >
            {isLoading ? (
              <div className="p-8">
                <LoadingState message="Loading tenders..." />
              </div>
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
                  </tr>
                </DataTableHeader>
                <DataTableBody>
                  {data?.data.map((tender) => (
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
                    </DataTableRow>
                  ))}
                </DataTableBody>
              </DataTable>
            )}
          </DataTableShell>
        </div>

        <div className="lg:col-span-2 space-y-4">
          <AiProcessingPipeline title="Live AI pipeline" steps={pipelineSteps} />
          <div className="surface-card p-5">
            <div className="flex items-center gap-2 text-primary mb-4">
              <Sparkles className="h-4 w-4" />
              <span className="text-sm font-semibold">Quick actions</span>
            </div>
            <div className="grid gap-2">
              <CanCreateTender>
                <Link
                  href="/dashboard/tenders/new"
                  className="flex items-center justify-between rounded-lg border border-border/60 p-3 text-sm font-medium transition-all hover:border-primary/30 hover:bg-primary/5"
                >
                  <span className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-primary" />
                    Create tender
                  </span>
                  <ArrowRight className="h-4 w-4 text-muted-foreground" />
                </Link>
              </CanCreateTender>
              <Link
                href="/dashboard/bids"
                className="flex items-center justify-between rounded-lg border border-border/60 p-3 text-sm font-medium transition-all hover:border-primary/30 hover:bg-primary/5"
              >
                <span className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-primary" />
                  Review bids
                </span>
                <ArrowRight className="h-4 w-4 text-muted-foreground" />
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
