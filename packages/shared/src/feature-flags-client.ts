/**
 * Client-safe feature flags (NEXT_PUBLIC_* only — no server env import).
 */

export type ClientFeatureFlagName =
  | 'ai_analysis'
  | 'document_ocr'
  | 'advanced_analytics'
  | 'webhooks'
  | 'api_access'
  | 'custom_domains'
  | 'sso';

const ENV_KEYS: Record<ClientFeatureFlagName, string> = {
  ai_analysis: 'NEXT_PUBLIC_FEATURE_AI_ANALYSIS',
  document_ocr: 'NEXT_PUBLIC_FEATURE_DOCUMENT_OCR',
  advanced_analytics: 'NEXT_PUBLIC_FEATURE_ADVANCED_ANALYTICS',
  webhooks: 'NEXT_PUBLIC_FEATURE_WEBHOOKS',
  api_access: 'NEXT_PUBLIC_FEATURE_API_ACCESS',
  custom_domains: 'NEXT_PUBLIC_FEATURE_CUSTOM_DOMAINS',
  sso: 'NEXT_PUBLIC_FEATURE_SSO',
};

const DEFAULTS: Record<ClientFeatureFlagName, boolean> = {
  ai_analysis: true,
  document_ocr: false,
  advanced_analytics: false,
  webhooks: true,
  api_access: true,
  custom_domains: false,
  sso: false,
};

function parseBool(raw: string | undefined, fallback: boolean): boolean {
  if (raw === undefined || raw === '') return fallback;
  const v = raw.toLowerCase();
  if (v === 'true' || v === '1' || v === 'yes') return true;
  if (v === 'false' || v === '0' || v === 'no') return false;
  return fallback;
}

export function isClientFeatureEnabled(flag: ClientFeatureFlagName): boolean {
  const key = ENV_KEYS[flag];
  const raw = typeof process !== 'undefined' ? process.env[key] : undefined;
  return parseBool(raw, DEFAULTS[flag]);
}

export function getClientFeatureDefaults(): Record<ClientFeatureFlagName, boolean> {
  return { ...DEFAULTS };
}
