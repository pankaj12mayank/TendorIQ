export const API_VERSION = 'v1';

export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
  UNPROCESSABLE_ENTITY: 422,
  TOO_MANY_REQUESTS: 429,
  INTERNAL_SERVER_ERROR: 500,
  SERVICE_UNAVAILABLE: 503,
} as const;

export const USER_ROLES = {
  SUPER_ADMIN: 'super_admin',
  OWNER: 'owner',
  ADMIN: 'admin',
  MANAGER: 'manager',
  ANALYST: 'analyst',
  MEMBER: 'member',
  VIEWER: 'viewer',
} as const;

export const USER_ROLE_VALUES = Object.values(USER_ROLES) as readonly string[];

export type UserRole = (typeof USER_ROLES)[keyof typeof USER_ROLES];

export const TENDER_STATUS = {
  DRAFT: 'draft',
  PUBLISHED: 'published',
  CLOSED: 'closed',
  CANCELLED: 'cancelled',
  AWARDED: 'awarded',
} as const;

export const BID_STATUS = {
  DRAFT: 'draft',
  SUBMITTED: 'submitted',
  UNDER_REVIEW: 'under_review',
  ACCEPTED: 'accepted',
  REJECTED: 'rejected',
  WITHDRAWN: 'withdrawn',
} as const;

export const FILE_TYPES = {
  DOCUMENT: 'document',
  IMAGE: 'image',
  PDF: 'pdf',
  SPREADSHEET: 'spreadsheet',
} as const;

export const PAGINATION = {
  DEFAULT_PAGE: 1,
  DEFAULT_LIMIT: 20,
  MAX_LIMIT: 100,
} as const;

export const CACHE_TTL = {
  SHORT: 60,
  MEDIUM: 300,
  LONG: 3600,
  VERY_LONG: 86400,
} as const;

export const RATE_LIMIT = {
  AUTH: { MAX: 10, WINDOW: 60 },
  API: { MAX: 100, WINDOW: 60 },
  UPLOAD: { MAX: 20, WINDOW: 3600 },
} as const;