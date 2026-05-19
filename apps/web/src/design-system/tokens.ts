/** TenderIQ design tokens — programmatic access */
export const roles = ['super_admin', 'tenant_admin', 'user'] as const;
export type AppRole = (typeof roles)[number];

export const statusTypes = [
  'processing',
  'retrying',
  'completed',
  'failed',
  'needs_review',
  'uploaded',
  'archived',
  'draft',
  'published',
] as const;
export type StatusType = (typeof statusTypes)[number];

export const motionDuration = {
  fast: 0.15,
  normal: 0.25,
  slow: 0.4,
} as const;

export const zIndex = {
  dropdown: 50,
  sticky: 40,
  modal: 100,
  toast: 110,
} as const;
