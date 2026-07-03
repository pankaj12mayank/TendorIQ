'use client';

import { useCallback, useEffect, useState } from 'react';
import { RefreshCw, Search, Trash2, Upload } from 'lucide-react';
import { appToast } from '@/lib/app-toast';

import { AdminRouteGuard } from '@/components/auth/admin-route-guard';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { LoadingState } from '@/components/ui/loading-state';
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
import { useAdminPlatform, type AdminUpload } from '@/hooks/use-admin-platform';

export default function AdminUploadsPage() {
  const [uploads, setUploads] = useState<AdminUpload[]>([]);
  const [uploadSearch, setUploadSearch] = useState('');
  const [uploadStatus, setUploadStatus] = useState('');
  const [uploadUserFilter, setUploadUserFilter] = useState('');
  const [selectedUploads, setSelectedUploads] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { loadUploads, deleteUpload, batchDeleteUploads } = useAdminPlatform();

  const loadUploadList = useCallback(async () => {
    const rows = await loadUploads({
      limit: 100, search: uploadSearch || undefined,
      status: uploadStatus || undefined, user_filter: uploadUserFilter || undefined,
    });
    setUploads(rows);
  }, [loadUploads, uploadSearch, uploadStatus, uploadUserFilter]);

  useEffect(() => {
    (async () => {
      try { await loadUploadList(); } catch (e) { setError(e instanceof Error ? e.message : 'Failed to load uploads'); } finally { setLoading(false); }
    })();
  }, [loadUploadList]);

  useEffect(() => { if (!loading) void loadUploadList(); }, [uploadSearch, uploadStatus, uploadUserFilter, loadUploadList, loading]);

  const toggleSelect = (id: string) => {
    setSelectedUploads((prev) => prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]);
  };

  const toggleAll = () => {
    if (selectedUploads.length === uploads.length) {
      setSelectedUploads([]);
    } else {
      setSelectedUploads(uploads.map((u) => u.id));
    }
  };

  if (loading) return <AdminRouteGuard><div className="w-full"><LoadingState message="Loading uploads..." /></div></AdminRouteGuard>;
  if (error) return <AdminRouteGuard><div className="w-full"><p className="text-sm text-destructive">{error}</p></div></AdminRouteGuard>;

  return (
    <AdminRouteGuard>
      <div className="w-full space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Upload history</h1>
          <p className="text-sm text-muted-foreground mt-1">All documents uploaded across all tenants</p>
        </div>
        <Card>
          <CardHeader className="pb-3">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <CardTitle className="text-base flex items-center gap-2">
                  <Upload className="h-4 w-4" />
                  Documents
                </CardTitle>
                <CardDescription>{uploads.length} uploads found</CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm" onClick={() => void loadUploadList()}>
                  <RefreshCw className="mr-1 h-3 w-3" />
                  Refresh
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  disabled={selectedUploads.length === 0}
                  onClick={async () => {
                    if (!confirm(`Delete ${selectedUploads.length} uploads?`)) return;
                    await batchDeleteUploads(selectedUploads);
                    setSelectedUploads([]);
                    await loadUploadList();
                    appToast.success('Selected uploads deleted.');
                  }}
                >
                  <Trash2 className="mr-1 h-3 w-3" />
                  Delete ({selectedUploads.length})
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-2 sm:grid-cols-3">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search files..."
                  value={uploadSearch}
                  onChange={(e) => setUploadSearch(e.target.value)}
                  className="pl-9"
                />
              </div>
              <Input
                placeholder="Filter by status..."
                value={uploadStatus}
                onChange={(e) => setUploadStatus(e.target.value)}
              />
              <Input
                placeholder="Filter by user email..."
                value={uploadUserFilter}
                onChange={(e) => setUploadUserFilter(e.target.value)}
              />
            </div>
            <DataTableShell>
              <DataTable>
                <DataTableHeader>
                  <DataTableRow>
                    <DataTableHead className="w-8">
                      <input
                        type="checkbox"
                        checked={uploads.length > 0 && selectedUploads.length === uploads.length}
                        onChange={toggleAll}
                        className="h-4 w-4"
                      />
                    </DataTableHead>
                    <DataTableHead>Name</DataTableHead>
                    <DataTableHead>Status</DataTableHead>
                    <DataTableHead>User</DataTableHead>
                    <DataTableHead>Tenant</DataTableHead>
                    <DataTableHead>Date</DataTableHead>
                    <DataTableHead className="text-right">Actions</DataTableHead>
                  </DataTableRow>
                </DataTableHeader>
                <DataTableBody>
                  {uploads.map((u) => (
                    <DataTableRow key={u.id}>
                      <DataTableCell>
                        <input
                          type="checkbox"
                          checked={selectedUploads.includes(u.id)}
                          onChange={() => toggleSelect(u.id)}
                          className="h-4 w-4"
                        />
                      </DataTableCell>
                      <DataTableCell className="font-medium">{u.name}</DataTableCell>
                      <DataTableCell>
                        <StatusBadge status={u.status as any} />
                      </DataTableCell>
                      <DataTableCell className="text-muted-foreground">{u.owner_email}</DataTableCell>
                      <DataTableCell className="text-muted-foreground">{u.tenant_name}</DataTableCell>
                      <DataTableCell className="text-muted-foreground">{new Date(u.created_at).toLocaleDateString()}</DataTableCell>
                      <DataTableCell>
                        <div className="flex justify-end">
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-destructive hover:text-destructive"
                            onClick={async () => {
                              if (!confirm('Delete this upload?')) return;
                              await deleteUpload(u.id);
                              await loadUploadList();
                            }}
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </DataTableCell>
                    </DataTableRow>
                  ))}
                  {uploads.length === 0 && (
                    <DataTableRow>
                      <DataTableCell colSpan={7} className="text-center text-muted-foreground py-8">
                        No uploads found.
                      </DataTableCell>
                    </DataTableRow>
                  )}
                </DataTableBody>
              </DataTable>
            </DataTableShell>
          </CardContent>
        </Card>
      </div>
    </AdminRouteGuard>
  );
}