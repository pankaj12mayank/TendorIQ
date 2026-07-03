'use client';

import { useCallback, useEffect, useState } from 'react';
import { Eye, Search, Shield, SlidersHorizontal, Trash2, UserX, UserCheck } from 'lucide-react';
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
import { useAdminPlatform, type PlatformUserRow } from '@/hooks/use-admin-platform';

type UserStatusFilter = 'all' | 'active' | 'inactive';

export default function AdminUsersPage() {
  const [users, setUsers] = useState<PlatformUserRow[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [selectedUserDetail, setSelectedUserDetail] = useState<Record<string, unknown> | null>(null);
  const [userSearch, setUserSearch] = useState('');
  const [userStatusFilter, setUserStatusFilter] = useState<UserStatusFilter>('all');
  const [usersPage, setUsersPage] = useState(1);
  const [usersMeta, setUsersMeta] = useState({ page: 1, pages: 0, total: 0, limit: 25 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { loadUsers, loadUserDetail, updateUserStatus, deleteUser } = useAdminPlatform();

  const fetchUsers = useCallback(async () => {
    const params: Record<string, string | number | undefined> = {
      search: userSearch, page: usersPage, limit: usersMeta.limit, include_deleted: 'true',
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
    setUsers(out.rows);
  }, [loadUsers, userSearch, userStatusFilter, usersPage, usersMeta.limit]);

  useEffect(() => {
    (async () => {
      try {
        const usersRes = await loadUsers({ page: 1, limit: 25, include_deleted: 'true' });
        setUsers(usersRes.rows ?? []);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load users');
      } finally {
        setLoading(false);
      }
    })();
  }, [loadUsers]);

  useEffect(() => { setUsersPage(1); }, [userSearch, userStatusFilter]);
  useEffect(() => { if (loading) return; void fetchUsers(); }, [loading, fetchUsers]);

  if (loading) return <AdminRouteGuard><div className="w-full"><LoadingState message="Loading users..." /></div></AdminRouteGuard>;
  if (error) return <AdminRouteGuard><div className="w-full"><p className="text-sm text-destructive">{error}</p></div></AdminRouteGuard>;

  const handleDetail = async (id: string) => {
    const d = await loadUserDetail(id);
    setSelectedUserId(id);
    setSelectedUserDetail(d);
  };

  return (
    <AdminRouteGuard>
      <div className="w-full space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">User management</h1>
          <p className="text-sm text-muted-foreground mt-1">Manage all registered users across workspaces</p>
        </div>
        <Card>
          <CardHeader className="pb-3">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <CardTitle className="text-base flex items-center gap-2">
                  <Shield className="h-4 w-4" />
                  Users
                </CardTitle>
                <CardDescription>{usersMeta.total} total users</CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <div className="flex rounded-lg border p-0.5">
                  {(['all', 'active', 'inactive'] as UserStatusFilter[]).map((chip) => (
                    <button
                      key={chip}
                      onClick={() => setUserStatusFilter(chip)}
                      className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                        userStatusFilter === chip
                          ? 'bg-primary text-primary-foreground'
                          : 'text-muted-foreground hover:text-foreground'
                      }`}
                    >
                      {chip === 'all' ? 'All' : chip === 'active' ? 'Active' : 'Inactive'}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search by name or email..."
                  value={userSearch}
                  onChange={(e) => setUserSearch(e.target.value)}
                  className="pl-9"
                />
              </div>
              <Button variant="outline" size="sm" onClick={fetchUsers}>
                <SlidersHorizontal className="mr-1 h-3 w-3" />
                Refresh
              </Button>
            </div>
            <DataTableShell>
              <DataTable>
                <DataTableHeader>
                  <DataTableRow>
                    <DataTableHead>Name</DataTableHead>
                    <DataTableHead>Email</DataTableHead>
                    <DataTableHead>Role</DataTableHead>
                    <DataTableHead>Plan</DataTableHead>
                    <DataTableHead>Organization</DataTableHead>
                    <DataTableHead>Status</DataTableHead>
                    <DataTableHead className="text-right">Actions</DataTableHead>
                  </DataTableRow>
                </DataTableHeader>
                <DataTableBody>
                  {users.map((u) => (
                    <DataTableRow key={u.id}>
                      <DataTableCell className="font-medium">{u.name}</DataTableCell>
                      <DataTableCell className="text-muted-foreground">{u.email}</DataTableCell>
                      <DataTableCell>
                        <Badge variant="outline" className="text-xs capitalize">{u.role}</Badge>
                      </DataTableCell>
                      <DataTableCell>
                        <Badge variant="secondary" className="text-xs">{u.plan ?? 'free'}</Badge>
                      </DataTableCell>
                      <DataTableCell className="text-muted-foreground">{u.organization}</DataTableCell>
                      <DataTableCell>
                        <Badge variant={u.status === 'active' ? 'success' : u.status === 'deleted' ? 'destructive' : 'warning'} className="text-xs capitalize">
                          {u.status === 'deleted' ? 'Deleted' : u.status}
                        </Badge>
                      </DataTableCell>
                      <DataTableCell>
                        <div className="flex items-center justify-end gap-1">
                          <Button size="sm" variant="ghost" onClick={() => handleDetail(u.id)} title="Details">
                            <Eye className="h-3.5 w-3.5" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={async () => {
                              const next = u.status === 'active' ? 'inactive' : 'active';
                              await updateUserStatus(u.id, next);
                              await fetchUsers();
                              appToast.success(`User ${next === 'inactive' ? 'suspended' : 'activated'}.`);
                            }}
                            title={u.status === 'active' ? 'Suspend' : 'Activate'}
                          >
                            {u.status === 'active' ? <UserX className="h-3.5 w-3.5" /> : <UserCheck className="h-3.5 w-3.5" />}
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-destructive hover:text-destructive"
                            onClick={async () => {
                              if (!confirm(`Permanently delete user ${u.email}?`)) return;
                              await deleteUser(u.id);
                              await fetchUsers();
                              if (selectedUserId === u.id) { setSelectedUserId(null); setSelectedUserDetail(null); }
                              appToast.success('User permanently deleted.');
                            }}
                            title="Delete"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </DataTableCell>
                    </DataTableRow>
                  ))}
                  {users.length === 0 && (
                    <DataTableRow>
                      <DataTableCell colSpan={7} className="text-center text-muted-foreground py-8">
                        No users found.
                      </DataTableCell>
                    </DataTableRow>
                  )}
                </DataTableBody>
              </DataTable>
            </DataTableShell>
            {usersMeta.pages > 1 && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">
                  Page {usersMeta.page} of {usersMeta.pages} ({usersMeta.total} users)
                </span>
                <div className="flex items-center gap-2">
                  <Button size="sm" variant="outline" disabled={usersPage <= 1} onClick={() => setUsersPage((p) => Math.max(1, p - 1))}>
                    Previous
                  </Button>
                  <Button size="sm" variant="outline" disabled={usersPage >= usersMeta.pages} onClick={() => setUsersPage((p) => Math.min(usersMeta.pages, p + 1))}>
                    Next
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
        {selectedUserId && selectedUserDetail && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">User details</CardTitle>
              <CardDescription>{selectedUserId}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {(['usage', 'uploads', 'analysis', 'proposals', 'payments', 'activity_timeline'] as const).map((key) => (
                  <div key={key} className="rounded-lg border p-3">
                    <h4 className="text-xs font-medium text-muted-foreground uppercase mb-2">{key.replace(/_/g, ' ')}</h4>
                    <pre className="text-xs max-h-[200px] overflow-auto whitespace-pre-wrap break-all">
                      {JSON.stringify((selectedUserDetail as any)[key] ?? {}, null, 2)}
                    </pre>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </AdminRouteGuard>
  );
}