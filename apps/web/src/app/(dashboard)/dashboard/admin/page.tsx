'use client';

import React, { useState, useEffect } from 'react';
import { useAdminStore } from '@/components/admin/store';
import { useAnalyticsStore } from '@/components/admin/store';
import { useAdminUsersApi, useBillingApi, useAIProvidersApi, usePromptsApi, useQueueApi, useAuditLogApi, useFailedJobsApi } from '@/hooks/use-admin';
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
  SystemHealth,
} from '@/components/admin/monitoring';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
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
  Settings,
  Bell,
  RefreshCw,
  Activity,
  Home,
} from 'lucide-react';
import { AdminModule } from '@/components/admin/types';
import { ADMIN_MODULES } from '@/components/admin/constants';
import { cn } from '@/lib/utils';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

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

interface RBACGuardProps {
  children: React.ReactNode;
  requiredPermissions?: string[];
  requiredRoles?: string[];
}

export function RBACGuard({ children, requiredPermissions = [], requiredRoles = [] }: RBACGuardProps) {
  const currentRole = 'admin';

  const hasPermission = requiredPermissions.length === 0 || 
    requiredPermissions.some(perm => perm === 'all' || currentRole === 'super_admin');

  const hasRole = requiredRoles.length === 0 || 
    requiredRoles.includes(currentRole);

  if (!hasPermission || !hasRole) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium mb-2">Access Denied</h3>
          <p className="text-muted-foreground">You don't have permission to access this section.</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

export default function AdminPage() {
  const router = useRouter();
  const { activeModule, setActiveModule, searchQuery, setSearchQuery, pagination, setPagination } = useAdminStore();
  const { metrics } = useAnalyticsStore();

  const [collapsed, setCollapsed] = useState(false);

  const { cards, isLoading: analyticsLoading, timeRange, setTimeRange, fetchMetrics, exportReport } = useAnalyticsApi();
  const { apiCalls, activeJobs, errorRate, avgResponseTime, subscribe, unsubscribe } = useRealtimeMetrics();

  useEffect(() => {
    subscribe();
    return () => unsubscribe();
  }, [subscribe, unsubscribe]);

  const renderModule = () => {
    switch (activeModule) {
      case 'users':
        return <UserManagement />;
      case 'billing':
        return <Billing />;
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
      <aside className={cn(
        'border-r bg-card flex flex-col transition-all duration-300',
        collapsed ? 'w-16' : 'w-64'
      )}>
        <div className="p-4 border-b flex items-center justify-between">
          {!collapsed && <h2 className="text-lg font-bold">Admin</h2>}
          <Button variant="ghost" size="sm" onClick={() => setCollapsed(!collapsed)}>
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </Button>
        </div>

        <nav className="flex-1 p-2 space-y-1">
          {ADMIN_MODULES.map((module) => {
            const Icon = MODULE_ICONS[module.id as keyof typeof MODULE_ICONS];
            const isActive = activeModule === module.id;

            return (
              <button
                key={module.id}
                onClick={() => setActiveModule(module.id as AdminModule)}
                className={cn(
                  'w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                )}
                title={collapsed ? module.label : undefined}
              >
                <Icon className="w-5 h-5 flex-shrink-0" />
                {!collapsed && <span>{module.label}</span>}
                {!collapsed && activeModule === module.id && (
                  <Badge variant="secondary" className="ml-auto text-xs">
                    {activeModule === 'users' && '28'}
                    {activeModule === 'billing' && '3'}
                    {activeModule === 'ai_settings' && '2'}
                    {activeModule === 'prompts' && '12'}
                    {activeModule === 'queue' && '17'}
                    {activeModule === 'audit' && '156'}
                    {activeModule === 'analytics' && ''}
                    {activeModule === 'failed_jobs' && '3'}
                  </Badge>
                )}
              </button>
            );
          })}
        </nav>

        <div className="p-2 border-t space-y-1">
          <Link href="/dashboard" className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-muted-foreground hover:bg-muted">
            <Home className="w-5 h-5" />
            {!collapsed && <span>Dashboard</span>}
          </Link>
          <Button variant="ghost" className={cn('w-full justify-start', collapsed && 'justify-center')}>
            <Settings className="w-5 h-5" />
            {!collapsed && <span>Settings</span>}
          </Button>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto">
        <div className="sticky top-0 z-10 bg-background border-b px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h1 className="text-2xl font-bold capitalize">{activeModule.replace('_', ' ')}</h1>
              <Badge variant="outline" className="text-xs">
                {activeModule === 'users' && `${metrics.totalUsers} users`}
                {activeModule === 'analytics' && 'Real-time'}
              </Badge>
            </div>

            <div className="flex items-center gap-4">
              {activeModule === 'analytics' && (
                <>
                  <RealtimeMetrics className="hidden lg:block" />
                  <RealtimeQueueStatus className="hidden lg:block" />
                </>
              )}
              
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  placeholder="Search..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-64 pl-10"
                />
              </div>

              <Button variant="outline" size="sm" onClick={() => fetchMetrics()}>
                <RefreshCw className={cn('w-4 h-4 mr-2', analyticsLoading && 'animate-spin')} />
                Refresh
              </Button>

              <Button variant="outline" size="sm">
                <Bell className="w-4 h-4 mr-2" />
                <span className="hidden lg:inline">Notifications</span>
              </Button>
            </div>
          </div>
        </div>

        <div className="p-6 space-y-6">
          {activeModule === 'analytics' && (
            <div className="grid gap-4 md:grid-cols-4">
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-muted-foreground">Total Users</span>
                    <Users className="w-4 h-4 text-muted-foreground" />
                  </div>
                  <div className="text-3xl font-bold mt-2">{metrics.totalUsers}</div>
                  <p className="text-xs text-green-600 mt-1">+12% from last month</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-muted-foreground">API Calls Today</span>
                    <Activity className="w-4 h-4 text-muted-foreground" />
                  </div>
                  <div className="text-3xl font-bold mt-2">{apiCalls.toLocaleString()}</div>
                  <p className="text-xs text-green-600 mt-1">Live count</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-muted-foreground">Active Jobs</span>
                    <RefreshCw className="w-4 h-4 text-muted-foreground" />
                  </div>
                  <div className="text-3xl font-bold mt-2">{activeJobs}</div>
                  <p className="text-xs text-muted-foreground mt-1">Processing</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-muted-foreground">Error Rate</span>
                    <AlertCircle className="w-4 h-4 text-muted-foreground" />
                  </div>
                  <div className="text-3xl font-bold mt-2">{errorRate.toFixed(1)}%</div>
                  <p className="text-xs text-muted-foreground mt-1">Last 24h</p>
                </CardContent>
              </Card>
            </div>
          )}

          {renderModule()}
        </div>

        <div className="sticky bottom-0 bg-background border-t px-6 py-3">
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>Page {pagination.page} of {pagination.totalPages}</span>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPagination({ page: Math.max(1, pagination.page - 1) })}
                disabled={pagination.page === 1}
              >
                <ChevronLeft className="w-4 h-4" />
              </Button>
              <span>{pagination.page} / {pagination.totalPages}</span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPagination({ page: Math.min(pagination.totalPages, pagination.page + 1) })}
                disabled={pagination.page === pagination.totalPages}
              >
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}