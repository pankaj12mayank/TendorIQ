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
import { Button } from '@/components/ui/button';
import { useTenders } from '@/hooks/use-api';
import { TableRowSkeleton } from '@/components/design-system/skeleton';
import { PremiumErrorState } from '@/components/design-system/empty-state';
import { staggerContainer, staggerItem } from '@/design-system/motion';
import { ROUTES } from '@/lib/routes';

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
  const organizationCount = new Set(
    tenders.map((t) => t.tenantId || t.organizationId).filter(Boolean)
  ).size;

  return (
    <div className="space-y-8">
      <PageHeader
        title="Dashboard"
        description="Upload tenders, run AI analysis, and generate proposals."
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

      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="show"
        className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"
      >
        <motion.div variants={staggerItem}>
          <KpiCard title="Active tenders" value={String(activeTenders)} trend={isLoading ? '...' : `${activeTenders > 0 ? '+' : ''}${activeTenders}`} trendUp icon={FileText} />
        </motion.div>
        <motion.div variants={staggerItem}>
          <KpiCard title="Organizations" value={String(organizationCount || '—')} trend="0%" icon={Users} />
        </motion.div>
        <motion.div variants={staggerItem}>
          <KpiCard title="Pipeline value" value={pipelineValue > 0 ? `$${(pipelineValue / 1000).toFixed(0)}K` : '—'} trend={isLoading ? '...' : '+'} trendUp icon={DollarSign} />
        </motion.div>
        <motion.div variants={staggerItem}>
          <KpiCard title="Total tenders" value={String(tenders.length)} trend={isLoading ? '...' : ''} icon={TrendingUp} />
        </motion.div>
      </motion.div>

      <div className="grid gap-6 lg:grid-cols-5">
        <div className="lg:col-span-3">
          <DataTableShell
            title="Recent tenders"
            description="Latest procurement activity across your workspace"
            toolbar={
              <Button variant="outline" size="sm" asChild>
                <Link href={ROUTES.upload}>Upload more</Link>
              </Button>
            }
          >
            {isLoading ? (
              <DataTable>
                <DataTableHeader>
                  <tr>
                    <DataTableHead>Title</DataTableHead>
                    <DataTableHead>Status</DataTableHead>
                    <DataTableHead>Created</DataTableHead>
                  </tr>
                </DataTableHeader>
                <DataTableBody>
                  {Array.from({ length: 5 }).map((_, i) => (
                    <TableRowSkeleton key={i} cols={3} />
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
              <Link
                href={ROUTES.analysis}
                className="flex items-center justify-between rounded-lg border border-border/60 p-3 text-sm font-medium transition-all hover:border-primary/30 hover:bg-primary/5"
              >
                <span className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-primary" />
                  View analysis
                </span>
                <ArrowRight className="h-4 w-4 text-muted-foreground" />
              </Link>
              <Link
                href={ROUTES.proposal}
                className="flex items-center justify-between rounded-lg border border-border/60 p-3 text-sm font-medium transition-all hover:border-primary/30 hover:bg-primary/5"
              >
                <span className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-primary" />
                  Draft proposal
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
