'use client';

import { type ReactNode } from 'react';
import { useAuthState } from '@/hooks/use-auth';

type Role = 'super_admin' | 'tenant_admin' | 'user';

interface RoleGuardProps {
  children: ReactNode;
  allowedRoles: Role[];
  fallback?: ReactNode;
}

export function RoleGuard({ children, allowedRoles, fallback }: RoleGuardProps) {
  const { user, isAuthenticated, isLoading } = useAuthState();

  if (isLoading) {
    return null;
  }

  if (!isAuthenticated) {
    return fallback ?? null;
  }

  const userRole = (user?.role || 'user') as Role;

  if (!allowedRoles.includes(userRole)) {
    return fallback ?? null;
  }

  return <>{children}</>;
}


interface PermissionGuardProps {
  children: ReactNode;
  permission: string;
  fallback?: ReactNode;
}

const rolePermissions: Record<string, string[]> = {
  super_admin: [
    'tender:*',
    'bid:*',
    'document:*',
    'org:*',
    'user:*',
    'settings:*',
    'analytics:*',
    'ai:*',
    'api:*',
  ],
  tenant_admin: [
    'tender:*',
    'bid:*',
    'document:*',
    'org:*',
    'user:*',
    'settings:*',
    'analytics:*',
    'ai:*',
    'api:*',
  ],
  user: [
    'tender:read',
    'tender:create',
    'bid:read',
    'bid:create',
    'document:read',
    'document:create',
    'org:read',
    'settings:read',
    'analytics:read',
    'ai:analysis',
  ],
};

export function PermissionGuard({ children, permission, fallback }: PermissionGuardProps) {
  const { user, isAuthenticated, isLoading } = useAuthState();

  if (isLoading) {
    return null;
  }

  if (!isAuthenticated) {
    return fallback ?? null;
  }

  const userRole = user?.role || 'user';
  const permissions = rolePermissions[userRole] || [];

  const hasPermission = permissions.some((p) => {
    if (p === permission) return true;
    if (p.endsWith(':*')) {
      const prefix = p.slice(0, -1);
      return permission.startsWith(prefix);
    }
    return false;
  });

  if (!hasPermission) {
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