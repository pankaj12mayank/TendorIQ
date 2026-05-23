import { useCallback, useState } from 'react';
import { toast } from 'sonner';

import { api } from '@/lib/api-client';
import { ADMIN_PLATFORM_PATHS } from '@/lib/admin-platform-paths';
import { parsePlatformUsersResponse } from '@/lib/admin-platform-api';
import { useAdminStore } from '@/components/admin/store';
import { User, UserRole, AdvancedFilter } from '@/components/admin/types';

import { reportAdminApiError } from './admin-api-errors';

export function useAdminUsersApi() {
  const { users, setUsers, isLoading, setLoading } = useAdminStore();
  const [isError, setIsError] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchUsers = useCallback(
    async (filters?: AdvancedFilter[]) => {
      setIsError(false);
      setError(null);
      setLoading(true);
      try {
        const params: Record<string, string | number | boolean> = {};
        if (filters?.length) {
          filters.forEach((f, i) => {
            params[`filter_${i}_field`] = f.field;
            params[`filter_${i}_op`] = f.operator;
            params[`filter_${i}_value`] = Array.isArray(f.value) ? f.value.join(',') : f.value;
          });
        }
        const res = await api.get<unknown>(ADMIN_PLATFORM_PATHS.users, { params });
        setUsers(parsePlatformUsersResponse(res).users);
      } catch (err) {
        setIsError(true);
        setError(reportAdminApiError(err, 'Failed to fetch users'));
      } finally {
        setLoading(false);
      }
    },
    [setUsers, setLoading]
  );

  const createUser = useCallback(
    async (userData: Partial<User>) => {
      setLoading(true);
      try {
        const created = await api.post<User>(ADMIN_PLATFORM_PATHS.users, {
          name: userData.name,
          email: userData.email,
          role: userData.role || 'viewer',
          status: userData.status || 'active',
          organization: userData.organization,
        });
        useAdminStore.getState().addUser(created);
        toast.success('User created successfully');
      } catch (err) {
        reportAdminApiError(err, 'Unable to create user');
      } finally {
        setLoading(false);
      }
    },
    [setLoading]
  );

  const updateUser = useCallback(
    async (id: string, data: Partial<User>) => {
      setLoading(true);
      try {
        const updated = await api.patch<User>(`${ADMIN_PLATFORM_PATHS.users}/${id}`, data);
        useAdminStore.getState().updateUser(id, updated);
        toast.success('User updated');
      } catch (err) {
        reportAdminApiError(err, 'Unable to save changes');
      } finally {
        setLoading(false);
      }
    },
    [setLoading]
  );

  const deleteUser = useCallback(
    async (id: string) => {
      setLoading(true);
      try {
        await api.delete(`${ADMIN_PLATFORM_PATHS.users}/${id}`);
        useAdminStore.getState().deleteUser(id);
        toast.success('User removed');
      } catch (err) {
        reportAdminApiError(err, 'Unable to delete user');
      } finally {
        setLoading(false);
      }
    },
    [setLoading]
  );

  const updateUserRole = useCallback(
    async (id: string, role: UserRole) => {
      await updateUser(id, { role });
    },
    [updateUser]
  );

  const toggleUserStatus = useCallback(
    async (id: string) => {
      const user = useAdminStore.getState().users.find((u) => u.id === id);
      if (!user) return;
      const newStatus = user.status === 'active' ? 'inactive' : 'active';
      await updateUser(id, { status: newStatus });
    },
    [updateUser]
  );

  return {
    users,
    isLoading,
    isError,
    error,
    fetchUsers,
    createUser,
    updateUser,
    deleteUser,
    updateUserRole,
    toggleUserStatus,
  };
}
