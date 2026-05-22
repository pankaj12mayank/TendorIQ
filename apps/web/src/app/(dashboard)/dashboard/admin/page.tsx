'use client';

import React, { Suspense, useState, useEffect, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAdminStore } from '@/components/admin/store';
import { useAnalyticsStore } from '@/components/admin/store';
import { useAnalyticsApi, useRealtimeMetrics } from '@/hooks/use-analytics';
import {
  UserManagement,
  Billing,
  AISettings,
  PromptManagement,
  QueueMonitoring,
  AuditLogs,
  UsageAnalytics,
  FailedJobs,
} from '@/components/admin';
import { EmailSystem } from '@/components/admin/email-system';
import {
  RealtimeQueueStatus,
  RealtimeMetrics,
} from '@/components/admin/monitoring';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Users,
  CreditCard,
  Cpu,
  MessageSquare,
  List,
  FileText,
  BarChart2,
  AlertCircle,
  Mail,
  Search,
  ChevronLeft,
  ChevronRight,
  Bell,
  RefreshCw,
  Activity,
  Home,
} from 'lucide-react';
import { AdminModule } from '@/components/admin/types';
import { ADMIN_MODULES } from '@/components/admin/constants';
import { cn } from '@/lib/utils';
import Link from 'next/link';
import { AdminRouteGuard } from '@/components/auth/admin-route-guard';
import { PlatformScopeBanner } from '@/components/admin/platform-scope-banner';
import { useCurrentUser } from '@/hooks/use-auth';
import { isSuperAdmin, hasPermission } from '@/lib/permissions';
import { LoadingState } from '@/components/ui/loading-state';

const MODULE_ICONS = {
  users: Users,
  billing: CreditCard,
  ai_settings: Cpu,
  prompts: MessageSquare,
  queue: List,
  audit: FileText,
  analytics: BarChart2,
  failed_jobs: AlertCircle,
  email_system: Mail,
};

const VALID_MODULES = new Set(ADMIN_MODULES.map((m) => m.id));

function RBACGuard({
  children,
  permission,
}: {
  children: React.ReactNode;
  permission?: string;
}) {
  const user = useCurrentUser();
  if (!isSuperAdmin(user?.role)) {
    return (
      <div className="flex h-64 items-center justify-center">
        <p className="text-muted-foreground">Super admin access required.</p>
      </div>
    );
  }
  if (permission && !hasPermission(user?.role, permission, user?.permissions)) {
    return (
      <div className="flex h-64 items-center justify-center">
        <p className="text-muted-foreground">You do not have permission for this section.</p>
      </div>
    );
  }
  return <>{children}</>;
}

function AdminConsoleContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { activeModule, setActiveModule, searchQuery, setSearchQuery, pagination, setPagination } =
    useAdminStore();
  const { metrics } = useAnalyticsStore();
  const [collapsed, setCollapsed] = useState(false);

  const { isLoading: analyticsLoading, fetchMetrics } = useAnalyticsApi();
  const { apiCalls, activeJobs, errorRate, subscribe, unsubscribe } = useRealtimeMetrics();

  const syncModuleFromUrl = useCallback(() => {
    const moduleParam = searchParams.get('module');
    if (moduleParam && VALID_MODULES.has(moduleParam)) {
      setActiveModule(moduleParam as AdminModule);
    }
  }, [searchParams, setActiveModule]);

  useEffect(() => {
    syncModuleFromUrl();
  }, [syncModuleFromUrl]);

  useEffect(() => {
    subscribe();
    return () => unsubscribe();
  }, [subscribe, unsubscribe]);

  const selectModule = (moduleId: AdminModule) => {
    setActiveModule(moduleId);
    router.replace(`/dashboard/admin?module=${moduleId}`, { scroll: false });
  };

  const renderModule = () => {
    switch (activeModule) {
      case 'users':
        return (
          <RBACGuard permission="user:read">
            <UserManagement />
          </RBACGuard>
        );
      case 'billing':
        return (
          <RBACGuard permission="billing:read">
            <Billing />
          </RBACGuard>
        );
      case 'ai_settings':
        return <AISettings />;
      case 'prompts':
        return <PromptManagement />;
      case 'queue':
        return <QueueMonitoring />;
      case 'audit':
        return <AuditLogs />;
      case 'analytics':
        return <UsageAnalytics />;
      case 'failed_jobs':
        return <FailedJobs />;
      case 'email_system':
        return <EmailSystem />;
      default:
        return <UserManagement />;
    }
  };

  return (
    <div className="flex h-[calc(100vh-64px)] bg-background">
      <aside
        className={cn(
          'flex flex-col border-r bg-card transition-all duration-300',
          collapsed ? 'w-16' : 'w-64'
        )}
      >
        <div className="flex items-center justify-between border-b p-4">
          {!collapsed && <h2 className="text-lg font-bold">Admin Console</h2>}
          <Button variant="ghost" size="sm" onClick={() => setCollapsed(!collapsed)}>
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </Button>
        </div>

        <nav className="flex-1 space-y-1 p-2">
          {ADMIN_MODULES.map((module) => {
            const Icon = MODULE_ICONS[module.id as keyof typeof MODULE_ICONS];
            const isActive = activeModule === module.id;

            return (
              <button
                key={module.id}
                type="button"
                onClick={() => selectModule(module.id as AdminModule)}
                className={cn(
                  'flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                )}
                title={collapsed ? module.label : undefined}
              >
                <Icon className="h-5 w-5 shrink-0" />
                {!collapsed && <span>{module.label}</span>}
              </button>
            );
          })}
        </nav>

        <div className="space-y-1 border-t p-2">
          <Link
            href="/"
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-muted"
          >
            <Home className="h-5 w-5" />
            {!collapsed && <span>Home</span>}
          </Link>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto">
        <div className="px-6 pt-4">
          <PlatformScopeBanner />
        </div>
        <div className="sticky top-0 z-10 border-b bg-background px-6 py-4">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <h1 className="text-2xl font-bold capitalize">
                {activeModule.replace(/_/g, ' ')}
              </h1>
              {activeModule === 'analytics' && (
                <Badge variant="outline" className="text-xs">
                  Real-time
                </Badge>
              )}
            </div>

            <div className="flex items-center gap-3">
              {activeModule === 'analytics' && (
                <>
                  <RealtimeMetrics className="hidden lg:block" />
                  <RealtimeQueueStatus className="hidden lg:block" />
                </>
              )}
              <div className="relative hidden md:block">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-64 pl-10"
                />
              </div>
              <Button variant="outline" size="sm" onClick={() => fetchMetrics()}>
                <RefreshCw
                  className={cn('mr-2 h-4 w-4', analyticsLoading && 'animate-spin')}
                />
                Refresh
              </Button>
              <Button variant="outline" size="sm" aria-label="Notifications">
                <Bell className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>

        <div className="space-y-6 p-6">
          {activeModule === 'analytics' && (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-muted-foreground">Total Users</span>
                    <Users className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div className="mt-2 text-3xl font-bold">{metrics.totalUsers}</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-muted-foreground">API Calls Today</span>
                    <Activity className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div className="mt-2 text-3xl font-bold">{apiCalls.toLocaleString()}</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-muted-foreground">Active Jobs</span>
                    <RefreshCw className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div className="mt-2 text-3xl font-bold">{activeJobs}</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-muted-foreground">Error Rate</span>
                    <AlertCircle className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div className="mt-2 text-3xl font-bold">{errorRate.toFixed(1)}%</div>
                </CardContent>
              </Card>
            </div>
          )}

          {renderModule()}
        </div>

        <div className="sticky bottom-0 border-t bg-background px-6 py-3">
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>
              Page {pagination.page} of {pagination.totalPages}
            </span>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPagination({ page: Math.max(1, pagination.page - 1) })}
                disabled={pagination.page === 1}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span>
                {pagination.page} / {pagination.totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  setPagination({
                    page: Math.min(pagination.totalPages, pagination.page + 1),
                  })
                }
                disabled={pagination.page === pagination.totalPages}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default function AdminPage() {
  return (
    <AdminRouteGuard>
      <Suspense
        fallback={
          <div className="flex min-h-[50vh] items-center justify-center">
            <LoadingState message="Loading admin console..." />
          </div>
        }
      >
        <AdminConsoleContent />
      </Suspense>
    </AdminRouteGuard>
  );
}
