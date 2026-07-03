'use client';

import { useState } from 'react';
import { BarChart3, Search, Activity } from 'lucide-react';
import { appToast } from '@/lib/app-toast';

import { AdminRouteGuard } from '@/components/auth/admin-route-guard';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  DataTableShell,
  DataTable,
  DataTableHeader,
  DataTableHead,
  DataTableBody,
  DataTableRow,
  DataTableCell,
} from '@/components/design-system/data-table';
import { useAdminPlatform } from '@/hooks/use-admin-platform';

export default function AdminAnalyticsPage() {
  const [analyticsQuery, setAnalyticsQuery] = useState('');
  const [analyticsRows, setAnalyticsRows] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const { searchAnalyticsUser } = useAdminPlatform();

  return (
    <AdminRouteGuard>
      <div className="w-full space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Analytics</h1>
          <p className="text-sm text-muted-foreground mt-1">Search and review user activity across the platform</p>
        </div>
        <Card>
          <CardHeader className="pb-3">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <CardTitle className="text-base flex items-center gap-2">
                  <BarChart3 className="h-4 w-4" />
                  Activity search
                </CardTitle>
                <CardDescription>Search by email to find user activity records</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search by email..."
                  value={analyticsQuery}
                  onChange={(e) => setAnalyticsQuery(e.target.value)}
                  className="pl-9"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      document.getElementById('analytics-search-btn')?.click();
                    }
                  }}
                />
              </div>
              <Button
                id="analytics-search-btn"
                variant="default"
                disabled={!analyticsQuery.trim() || loading}
                onClick={async () => {
                  if (!analyticsQuery.trim()) return;
                  setLoading(true);
                  setSearched(true);
                  try {
                    const res = await searchAnalyticsUser(analyticsQuery.trim()) as any;
                    setAnalyticsRows(res?.data ?? []);
                    if (!res?.data?.length) {
                      appToast.info('No activity found for this user.');
                    }
                  } catch (e) {
                    appToast.error(e instanceof Error ? e.message : 'Search failed');
                  } finally {
                    setLoading(false);
                  }
                }}
              >
                {loading ? (
                  <span className="flex items-center gap-1">
                    <Activity className="h-3 w-3 animate-pulse" />
                    Searching...
                  </span>
                ) : (
                  <span className="flex items-center gap-1">
                    <Search className="h-3 w-3" />
                    Search
                  </span>
                )}
              </Button>
            </div>
            {searched && analyticsRows.length > 0 && (
              <DataTableShell>
                <DataTable>
                  <DataTableHeader>
                    <DataTableRow>
                      <DataTableHead>Action</DataTableHead>
                      <DataTableHead>Date</DataTableHead>
                      <DataTableHead>Details</DataTableHead>
                    </DataTableRow>
                  </DataTableHeader>
                  <DataTableBody>
                    {analyticsRows.map((row, i) => (
                      <DataTableRow key={i}>
                        <DataTableCell>
                          <Badge variant="outline" className="text-xs">{String(row.action ?? '')}</Badge>
                        </DataTableCell>
                        <DataTableCell className="text-muted-foreground">
                          {row.created_at ? new Date(String(row.created_at)).toLocaleString() : '—'}
                        </DataTableCell>
                        <DataTableCell className="text-muted-foreground max-w-md truncate">
                          {String(row.detail ?? '')}
                        </DataTableCell>
                      </DataTableRow>
                    ))}
                  </DataTableBody>
                </DataTable>
              </DataTableShell>
            )}
            {searched && analyticsRows.length === 0 && (
              <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                <Activity className="h-8 w-8 mb-2 opacity-40" />
                <p className="text-sm">No activity found for <strong>{analyticsQuery}</strong></p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </AdminRouteGuard>
  );
}