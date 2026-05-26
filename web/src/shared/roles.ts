/**
 * Canonical role strings — align admin UI, auth session, and RBAC matrix.
 */

import { membershipRoleSchema } from './types/index.js';
import type { z } from 'zod';

export type MembershipRole = z.infer<typeof membershipRoleSchema>;

/** Roles shown in super-admin user management (platform + all membership roles). */
export type AdminConsoleRole = MembershipRole | 'super_admin';

export const MEMBERSHIP_ROLES = membershipRoleSchema.options;

export const ADMIN_CONSOLE_ROLES: AdminConsoleRole[] = [
  'super_admin',
  'owner',
  'admin',
  'manager',
  'analyst',
  'member',
  'viewer',
];

const ALIASES: Record<string, MembershipRole | 'super_admin'> = {
  super_admin: 'super_admin',
  tenant_admin: 'admin',
  user: 'member',
};

export function normalizeDisplayRole(role: string | undefined): AdminConsoleRole | undefined {
  if (!role) return undefined;
  const key = role.trim().toLowerCase();
  if (key in ALIASES) return ALIASES[key];
  if ((MEMBERSHIP_ROLES as readonly string[]).includes(key)) {
    return key as MembershipRole;
  }
  return undefined;
}

export function isMembershipRole(role: string): role is MembershipRole {
  return (MEMBERSHIP_ROLES as readonly string[]).includes(role);
}
