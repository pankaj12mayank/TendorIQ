import { z } from 'zod';

// ===========================================
// ENVIRONMENT SCHEMA - Comprehensive Validation
// ===========================================

export const envSchema = z.object({
  // ===========================================
  // COMMON / SHARED
  // ===========================================
  NODE_ENV: z.enum(['development', 'staging', 'production']).default('development'),
  LOG_LEVEL: z.enum(['debug', 'info', 'warn', 'error']).default('debug'),
  APP_NAME: z.string().default('TenderIQ'),
  APP_URL: z.string().url().default('http://localhost:3000'),

  // ===========================================
  // DATABASE - MySQL
  // ===========================================
  DATABASE_URL: z.string(),
  DATABASE_HOST: z.string().default('localhost'),
  DATABASE_PORT: z.coerce.number().default(3306),
  DATABASE_NAME: z.string().default('tendoriq'),
  DATABASE_USER: z.string().default('root'),
  DATABASE_PASSWORD: z.string().optional(),
  DATABASE_POOL_SIZE: z.coerce.number().min(1).max(100).default(10),
  DATABASE_MAX_OVERFLOW: z.coerce.number().min(0).max(100).default(20),
  DATABASE_ECHO: z.coerce.boolean().default(false),

  // ===========================================
  // REDIS - Queue & Cache (optional, removed from default stack)
  // ===========================================
  REDIS_HOST: z.string().default('localhost'),
  REDIS_PORT: z.coerce.number().min(1).max(65535).default(6379),
  REDIS_DB: z.coerce.number().min(0).max(15).default(0),
  REDIS_PASSWORD: z.string().optional(),
  REDIS_URL: z.string().optional(),

  // ===========================================
  // AUTH - Clerk (Primary) or Supabase (Alternative)
  // ===========================================
  AUTH_PROVIDER: z.enum(['clerk', 'supabase']).default('clerk'),

  // Clerk
  NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: z.string().optional(),
  CLERK_SECRET_KEY: z.string().min(1).optional(),
  CLERK_WEBHOOK_SECRET: z.string().min(1).optional(),
  NEXT_PUBLIC_CLERK_SIGN_IN_URL: z.string().default('/sign-in'),
  NEXT_PUBLIC_CLERK_SIGN_UP_URL: z.string().default('/sign-up'),
  NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL: z.string().default('/dashboard'),
  NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL: z.string().default('/dashboard'),

  // Supabase
  NEXT_PUBLIC_SUPABASE_URL: z.string().url().optional(),
  NEXT_PUBLIC_SUPABASE_ANON_KEY: z.string().optional(),
  SUPABASE_SERVICE_ROLE_KEY: z.string().optional(),

  // JWT
  JWT_SECRET: z.string().min(32),
  JWT_ALGORITHM: z.string().default('HS256'),
  JWT_ACCESS_TOKEN_EXPIRE_MINUTES: z.coerce.number().default(30),
  JWT_REFRESH_TOKEN_EXPIRE_DAYS: z.coerce.number().default(7),

  // ===========================================
  // API - FastAPI Backend
  // ===========================================
  API_HOST: z.string().default('0.0.0.0'),
  API_PORT: z.coerce.number().min(1).max(65535).default(8000),
  API_RELOAD: z.coerce.boolean().default(true),
  API_WORKERS: z.coerce.number().min(1).max(32).default(1),
  API_CORS_ORIGINS: z.string().default('http://localhost:3000'),
  API_PREFIX: z.string().default('/api/v1'),

  // ===========================================
  // FRONTEND - Next.js
  // ===========================================
  NEXT_PUBLIC_APP_URL: z.string().url().default('http://localhost:3000'),
  NEXT_PUBLIC_API_URL: z.string().url().default('http://localhost:8000'),
  NEXT_PUBLIC_APP_NAME: z.string().default('TenderIQ'),

  // ===========================================
  // STORAGE - AWS S3 / Cloudflare R2
  // ===========================================
  STORAGE_PROVIDER: z.enum(['s3', 'r2', 'local']).default('local'),
  AWS_ACCESS_KEY_ID: z.string().optional(),
  AWS_SECRET_ACCESS_KEY: z.string().optional(),
  AWS_REGION: z.string().default('us-east-1'),
  AWS_S3_BUCKET: z.string().optional(),
  AWS_ENDPOINT_URL: z.string().url().optional(), // For R2

  // ===========================================
  // AI - OpenAI / Anthropic / Azure
  // ===========================================
  AI_PROVIDER: z.enum(['openai', 'anthropic', 'azure']).default('openai'),
  AI_API_KEY: z.string().optional(),
  AI_MODEL: z.string().default('gpt-4'),
  AI_MAX_TOKENS: z.coerce.number().default(4000),
  AI_TEMPERATURE: z.coerce.number().min(0).max(2).default(0.7),

  // Azure-specific
  AZURE_OPENAI_ENDPOINT: z.string().url().optional(),
  AZURE_OPENAI_DEPLOYMENT_NAME: z.string().optional(),

  // ===========================================
  // EMAIL - Resend (Primary) / SendGrid / SMTP
  // ===========================================
  EMAIL_PROVIDER: z.enum(['resend', 'sendgrid', 'smtp']).default('resend'),
  EMAIL_API_KEY: z.string().optional(),
  EMAIL_FROM: z.string().email().default('noreply@tendoriq.com'),
  EMAIL_FROM_NAME: z.string().default('TenderIQ'),

  // SMTP
  SMTP_HOST: z.string().optional(),
  SMTP_PORT: z.coerce.number().default(587),
  SMTP_USER: z.string().optional(),
  SMTP_PASSWORD: z.string().optional(),

  // ===========================================
  // OBSERVABILITY - Sentry
  // ===========================================
  SENTRY_DSN: z.string().url().optional(),
  SENTRY_ENVIRONMENT: z.string().default('development'),
  SENTRY_TRACES_SAMPLE_RATE: z.coerce.number().min(0).max(1).default(1),
  SENTRY_PROFILING_SAMPLE_RATE: z.coerce.number().min(0).max(1).default(0),

  // ===========================================
  // RATE LIMITING
  // ===========================================
  RATE_LIMIT_ENABLED: z.coerce.boolean().default(true),
  RATE_LIMIT_PER_MINUTE: z.coerce.number().default(60),
  RATE_LIMIT_PER_HOUR: z.coerce.number().default(1000),

  // ===========================================
  // FEATURE FLAGS
  // ===========================================
  FEATURE_AI_ANALYSIS: z.coerce.boolean().default(true),
  FEATURE_DOCUMENT_OCR: z.coerce.boolean().default(false),
  FEATURE_ADVANCED_ANALYTICS: z.coerce.boolean().default(false),
  FEATURE_WEBHOOKS: z.coerce.boolean().default(true),
  FEATURE_API_ACCESS: z.coerce.boolean().default(true),
  FEATURE_CUSTOM_DOMAINS: z.coerce.boolean().default(false),
  FEATURE_SSO: z.coerce.boolean().default(false),

  // ===========================================
  // RAILWAY-SPECIFIC
  // ===========================================
  RAILWAY_SERVICE_NAME: z.string().optional(),
  RAILWAY_PUBLIC_DOMAIN: z.string().url().optional(),
  RAILWAY_DEPLOYMENT_ID: z.string().optional(),
  RAILWAY_PROJECT_ID: z.string().optional(),

  // ===========================================
  // VERCEL-SPECIFIC
  // ===========================================
  VERCEL: z.coerce.boolean().default(false),
  VERCEL_ENV: z.string().optional(),
  VERCEL_GIT_COMMIT_REF: z.string().optional(),
  VERCEL_GIT_COMMIT_SHA: z.string().optional(),
  VERCEL_DEPLOYMENT_URL: z.string().optional(),

  // ===========================================
  // INTERNAL
  // ===========================================
  INTERNAL_API_KEY: z.string().optional(),
  ENCRYPTION_KEY: z.string().optional(),
});

export type Env = z.infer<typeof envSchema>;

// ===========================================
// ENVIRONMENT LOADING
// ===========================================

function getDefaultValue(key: string): string | undefined {
  const defaults: Record<string, string> = {
    NODE_ENV: 'development',
    LOG_LEVEL: 'debug',
    APP_NAME: 'TenderIQ',
    APP_URL: 'http://localhost:3000',
    DATABASE_HOST: 'localhost',
    DATABASE_PORT: '3306',
    DATABASE_NAME: 'tendoriq',
    DATABASE_USER: 'root',
    DATABASE_POOL_SIZE: '10',
    DATABASE_MAX_OVERFLOW: '20',
    DATABASE_ECHO: 'false',
    REDIS_HOST: 'localhost',
    REDIS_PORT: '6379',
    REDIS_DB: '0',
    AUTH_PROVIDER: 'clerk',
    NEXT_PUBLIC_CLERK_SIGN_IN_URL: '/sign-in',
    NEXT_PUBLIC_CLERK_SIGN_UP_URL: '/sign-up',
    NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL: '/dashboard',
    NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL: '/dashboard',
    JWT_ALGORITHM: 'HS256',
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: '30',
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: '7',
    API_HOST: '0.0.0.0',
    API_PORT: '8000',
    API_RELOAD: 'true',
    API_WORKERS: '1',
    API_CORS_ORIGINS: 'http://localhost:3000',
    API_PREFIX: '/api/v1',
    NEXT_PUBLIC_APP_URL: 'http://localhost:3000',
    NEXT_PUBLIC_API_URL: 'http://localhost:8000',
    NEXT_PUBLIC_APP_NAME: 'TenderIQ',
    STORAGE_PROVIDER: 'local',
    AWS_REGION: 'us-east-1',
    AI_PROVIDER: 'openai',
    AI_MODEL: 'gpt-4',
    AI_MAX_TOKENS: '4000',
    AI_TEMPERATURE: '0.7',
    EMAIL_PROVIDER: 'resend',
    EMAIL_FROM: 'noreply@tendoriq.com',
    EMAIL_FROM_NAME: 'TenderIQ',
    SMTP_PORT: '587',
    SENTRY_ENVIRONMENT: 'development',
    SENTRY_TRACES_SAMPLE_RATE: '1',
    SENTRY_PROFILING_SAMPLE_RATE: '0',
    RATE_LIMIT_ENABLED: 'true',
    RATE_LIMIT_PER_MINUTE: '60',
    RATE_LIMIT_PER_HOUR: '1000',
    FEATURE_AI_ANALYSIS: 'true',
    FEATURE_DOCUMENT_OCR: 'false',
    FEATURE_ADVANCED_ANALYTICS: 'false',
    FEATURE_WEBHOOKS: 'true',
    FEATURE_API_ACCESS: 'true',
    FEATURE_CUSTOM_DOMAINS: 'false',
    FEATURE_SSO: 'false',
    VERCEL: 'false',
  };

  return defaults[key];
}

function buildEnvData(): Record<string, unknown> {
  const data: Record<string, unknown> = {};

  for (const key of Object.keys(envSchema.shape)) {
    const defaultValue = getDefaultValue(key);

    data[key] = process.env[key] ?? defaultValue ?? null;
  }

  // Build DATABASE_URL from components if not provided
  if (!data.DATABASE_URL && data.DATABASE_HOST) {
    const user = data.DATABASE_USER || 'root';
    const pwPart = data.DATABASE_PASSWORD ? `:${data.DATABASE_PASSWORD}` : '';
    const host = data.DATABASE_HOST;
    const port = data.DATABASE_PORT || 3306;
    const name = data.DATABASE_NAME || 'tendoriq';
    data.DATABASE_URL = `mysql+aiomysql://${user}${pwPart}@${host}:${port}/${name}?charset=utf8mb4`;
  }

  // Build REDIS_URL from components (optional)
  if (!data.REDIS_URL && data.REDIS_HOST) {
    const pwPart = data.REDIS_PASSWORD ? `:${data.REDIS_PASSWORD}@` : '';
    const host = data.REDIS_HOST;
    const port = data.REDIS_PORT || 6379;
    const db = data.REDIS_DB || 0;
    data.REDIS_URL = `redis://${pwPart}${host}:${port}/${db}`;
  }

  return data;
}

let _env: Env | null = null;

export function getEnv(): Env {
  if (_env) return _env;

  const envData = buildEnvData();
  const result = envSchema.safeParse(envData);

  if (!result.success) {
    const errors = result.error.flatten().fieldErrors;
    console.error('Environment validation failed:');
    console.error(JSON.stringify(errors, null, 2));
    throw new Error('Missing or invalid environment variables');
  }

  _env = result.data;
  return _env;
}

export const env = getEnv();

// ===========================================
// BOOLEAN FLAGS
// ===========================================

export const isDev = env.NODE_ENV === 'development';
export const isStaging = env.NODE_ENV === 'staging';
export const isProd = env.NODE_ENV === 'production';

export const isRailway = !!env.RAILWAY_SERVICE_NAME;
export const isVercel = env.VERCEL || !!process.env.VERCEL_DEPLOYMENT_URL;

// ===========================================
// DERIVED VALUES
// ===========================================

export function getAppUrl(): string {
  if (isRailway && env.RAILWAY_PUBLIC_DOMAIN) {
    return `https://${env.RAILWAY_PUBLIC_DOMAIN}`;
  }
  if (isVercel && env.VERCEL_DEPLOYMENT_URL) {
    return `https://${env.VERCEL_DEPLOYMENT_URL}`;
  }
  return env.APP_URL;
}

export function getApiUrl(): string {
  if (isRailway && env.RAILWAY_PUBLIC_DOMAIN) {
    return `https://${env.RAILWAY_PUBLIC_DOMAIN}`;
  }
  if (isVercel) {
    return process.env.NEXT_PUBLIC_API_URL || `https://${env.VERCEL_DEPLOYMENT_URL}/api`;
  }
  return env.NEXT_PUBLIC_API_URL;
}

export function getDatabaseUrl(): string {
  return env.DATABASE_URL;
}

export function getRedisUrl(): string {
  return env.REDIS_URL || `redis://${env.REDIS_HOST}:${env.REDIS_PORT}/${env.REDIS_DB}`;
}

// ===========================================
// FEATURE FLAGS
// ===========================================

export const features = {
  aiAnalysis: env.FEATURE_AI_ANALYSIS,
  documentOcr: env.FEATURE_DOCUMENT_OCR,
  advancedAnalytics: env.FEATURE_ADVANCED_ANALYTICS,
  webhooks: env.FEATURE_WEBHOOKS,
  apiAccess: env.FEATURE_API_ACCESS,
  customDomains: env.FEATURE_CUSTOM_DOMAINS,
  sso: env.FEATURE_SSO,
};

export function isFeatureEnabled(feature: keyof typeof features): boolean {
  return features[feature];
}