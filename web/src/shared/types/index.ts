import { z } from 'zod';

import { normalizeBillingCycle, normalizePlanId } from '../plans.js';

/** Platform role (JWT) or effective tenant role for display. */
export const platformRoleSchema = z.enum(['super_admin', 'user']);

/** Tenant membership roles — matches DB memberships.role CHECK. */
export const membershipRoleSchema = z.enum([
  'owner',
  'admin',
  'manager',
  'analyst',
  'member',
  'viewer',
]);

export const userSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  name: z.string().min(1).max(255).optional(),
  /** Effective role for UI (super_admin or membership role). */
  role: z.union([platformRoleSchema, membershipRoleSchema]),
  membershipRole: membershipRoleSchema.optional(),
  tenantId: z.string().uuid().optional(),
  avatarUrl: z.string().url().optional(),
  createdAt: z.date(),
  updatedAt: z.date(),
});

export type User = z.infer<typeof userSchema>;
export type MembershipRole = z.infer<typeof membershipRoleSchema>;
export type PlatformRole = z.infer<typeof platformRoleSchema>;

export const tenderSchema = z.object({
  id: z.string().uuid(),
  title: z.string().min(1).max(500),
  description: z.string().min(1),
  status: z.enum(['draft', 'published', 'closed', 'cancelled', 'awarded']),
  budget: z.number().min(0).nullable(),
  currency: z.string().length(3).default('USD'),
  closingDate: z.date().nullable(),
  createdById: z.string().uuid(),
  /** Tenant that owns the tender (matches API `tenant_id`). */
  tenantId: z.string().uuid(),
  /** @deprecated Use tenantId */
  organizationId: z.string().uuid().optional(),
  createdAt: z.date(),
  updatedAt: z.date(),
});

export type Tender = z.infer<typeof tenderSchema>;

export const bidSchema = z.object({
  id: z.string().uuid(),
  tenderId: z.string().uuid(),
  bidderId: z.string().uuid(),
  amount: z.number().min(0),
  currency: z.string().length(3).default('USD'),
  status: z.enum(['draft', 'submitted', 'under_review', 'accepted', 'rejected', 'withdrawn']),
  proposal: z.string().optional(),
  documents: z.array(z.string().url()).default([]),
  submittedAt: z.date().nullable(),
  createdAt: z.date(),
  updatedAt: z.date(),
});

export type Bid = z.infer<typeof bidSchema>;

export const organizationSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1).max(255),
  slug: z.string().min(1).max(100).regex(/^[a-z0-9-]+$/),
  logo: z.string().url().optional(),
  description: z.string().optional(),
  website: z.string().url().optional(),
  createdAt: z.date(),
  updatedAt: z.date(),
});

export type Organization = z.infer<typeof organizationSchema>;

export const apiResponseSchema = <T extends z.ZodTypeAny>(dataSchema: T) =>
  z.object({
    success: z.boolean(),
    data: dataSchema.optional(),
    error: z
      .object({
        code: z.string(),
        message: z.string(),
        details: z.record(z.string(), z.unknown()).optional(),
      })
      .optional(),
    meta: z
      .object({
        page: z.number().int().positive().default(1),
        limit: z.number().int().positive().default(20),
        total: z.number().int().nonnegative().optional(),
        totalPages: z.number().int().nonnegative().optional(),
      })
      .optional(),
  });

export type ApiResponse<T> = z.infer<ReturnType<typeof apiResponseSchema<z.ZodType<T>>>>;

export const paginationSchema = z.object({
  page: z.number().int().positive().default(1),
  limit: z.number().int().positive().max(100).default(20),
  sort: z.string().optional(),
  order: z.enum(['asc', 'desc']).default('desc'),
});

export type Pagination = z.infer<typeof paginationSchema>;

export interface BaseEntity {
  id: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface AuditableEntity extends BaseEntity {
  createdById: string;
  updatedById: string;
}

export const onboardingStateSchema = z.object({
  id: z.string().uuid(),
  userId: z.string().uuid(),
  tenantId: z.string().uuid().optional(),
  currentStep: z.number().int().min(1).max(5).default(1),
  totalSteps: z.number().int().default(5),
  step1Completed: z.boolean().default(false),
  step2Completed: z.boolean().default(false),
  step3Completed: z.boolean().default(false),
  step4Completed: z.boolean().default(false),
  step5Completed: z.boolean().default(false),
  isCompleted: z.boolean().default(false),
  completedAt: z.date().optional(),
});

export type OnboardingState = z.infer<typeof onboardingStateSchema>;

export const step1Schema = z.object({
  name: z.string().min(2).max(255),
  slug: z.string().min(2).max(100).regex(/^[a-z0-9-]+$/),
  logoUrl: z.string().url().optional(),
});

export type Step1Data = z.infer<typeof step1Schema>;

export const step2Schema = z.object({
  description: z.string().max(2000).optional(),
  website: z.string().url().optional(),
  industry: z.string().optional(),
  companySize: z.string().optional(),
  foundedYear: z.number().int().min(1800).max(2100).optional(),
  headquarters: z.string().optional(),
  phone: z.string().optional(),
  address: z.string().optional(),
});

export type Step2Data = z.infer<typeof step2Schema>;

export const step3Schema = z.object({
  expertiseAreas: z.array(z.string()).default([]),
  customExpertise: z.string().max(500).optional(),
  annualTenderVolume: z.string().optional(),
  averageContractValue: z.string().optional(),
  targetRegions: z.array(z.string()).default([]),
  certifications: z.array(z.string()).default([]),
});

export type Step3Data = z.infer<typeof step3Schema>;

export const step4Schema = z.object({
  planId: z
    .string()
    .transform((v) => normalizePlanId(v))
    .pipe(z.enum(['free', 'starter', 'professional', 'enterprise'])),
  billingCycle: z
    .string()
    .transform((v) => normalizeBillingCycle(v))
    .pipe(z.enum(['monthly', 'yearly']))
    .default('monthly'),
  addons: z.array(z.string()).default([]),
});

export type Step4Data = z.infer<typeof step4Schema>;

export const step5Schema = z.object({
  notificationsEnabled: z.boolean().default(true),
  emailDigest: z.enum(['daily', 'weekly', 'monthly', 'never']).default('weekly'),
  timezone: z.string().default('UTC'),
  currency: z.string().length(3).default('USD'),
  language: z.string().default('en'),
});

export type Step5Data = z.infer<typeof step5Schema>;