'use client';

import { type ReactNode } from 'react';
import { GuardLoadingPlaceholder } from '@/components/layout/dashboard-loading';
import { useAuthState } from '@/hooks/use-auth';
import { getMembershipRole } from '@/lib/auth-user';
import { hasPermission, isSuperAdmin } from '@/lib/permissions';

type Role =
  | 'super_admin'
  | 'owner'
  | 'admin'
  | 'tenant_admin'
  | 'manager'
  | 'analyst'
  | 'member'
  | 'viewer';

interface RoleGuardProps {
  children: ReactNode;
  allowedRoles: Role[];
  fallback?: ReactNode;
}

export function RoleGuard({ children, allowedRoles, fallback }: RoleGuardProps) {
  const { user, isAuthenticated, isLoading } = useAuthState();

  if (isLoading) {
    return fallback ?? <GuardLoadingPlaceholder />;
  }

  if (!isAuthenticated) {
    return fallback ?? null;
  }

  const userRole = (getMembershipRole(user) || 'viewer') as Role;
  const platformRole = user?.role;
  const effectiveRoles = platformRole && isSuperAdmin(platformRole)
    ? (['super_admin'] as Role[])
    : ([userRole] as Role[]);

  if (!allowedRoles.some((r) => effectiveRoles.includes(r))) {
    return fallback ?? null;
  }

  return <>{children}</>;
}

interface PermissionGuardProps {
  children: ReactNode;
  permission: string;
  fallback?: ReactNode;
}

export function PermissionGuard({ children, permission, fallback }: PermissionGuardProps) {
  const { user, isAuthenticated, isLoading } = useAuthState();

  if (isLoading) {
    return fallback ?? <GuardLoadingPlaceholder />;
  }

  if (!isAuthenticated) {
    return fallback ?? null;
  }

  const allowed = hasPermission(getMembershipRole(user), permission, user?.permissions);

  if (!allowed) {
    return fallback ?? null;
  }

  return <>{children}</>;
}

export function CanCreateTender({ children, fallback }: { children: ReactNode; fallback?: ReactNode }) {
  return (
    <PermissionGuard permission="tender:create" fallback={fallback}>
      {children}
    </PermissionGuard>
  );
}

export function CanDeleteTender({ children, fallback }: { children: ReactNode; fallback?: ReactNode }) {
  return (
    <PermissionGuard permission="tender:delete" fallback={fallback}>
      {children}
    </PermissionGuard>
  );
}

export function CanManageUsers({ children, fallback }: { children: ReactNode; fallback?: ReactNode }) {
  return (
    <PermissionGuard permission="user:manage" fallback={fallback}>
      {children}
    </PermissionGuard>
  );
}

export function CanViewAnalytics({ children, fallback }: { children: ReactNode; fallback?: ReactNode }) {
  return (
    <PermissionGuard permission="analytics:view" fallback={fallback}>
      {children}
    </PermissionGuard>
  );
}

export function CanUseAI({ children, fallback }: { children: ReactNode; fallback?: ReactNode }) {
  return (
    <PermissionGuard permission="ai:analysis" fallback={fallback}>
      {children}
    </PermissionGuard>
  );
}
