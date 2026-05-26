/**
 * Browser session user — subset of API /auth/me (not the full shared User zod model).
 */

import type { MembershipRole } from './roles.js';

export interface SessionUser {
  id: string;
  email: string;
  name: string;
  imageUrl?: string;
  /** Platform (`super_admin`) or legacy display role from API. */
  role?: string;
  membershipRole?: MembershipRole | string;
  tenantId?: string;
  permissions?: string[];
  companyProfile?: {
    company_name?: string;
    [key: string]: unknown;
  };
}
