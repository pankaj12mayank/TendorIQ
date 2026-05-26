/** Lite feature flags — client-safe defaults. */

export type ClientFeatureFlagName = 'sso' | 'clerk' | 'analytics';

/** Product flags driven by NEXT_PUBLIC_FEATURE_* (sidebar / client UI). */
export type ProductFeatureFlagName = 'aiAnalysis' | 'documentOcr' | 'advancedAnalytics';

/** Nav href (path only) → product feature required to show the link. */
export const NAV_ITEM_FEATURES: Partial<Record<string, ProductFeatureFlagName>> = {
  '/dashboard/analysis': 'aiAnalysis',
  '/dashboard/proposal': 'aiAnalysis',
};

const DEFAULTS: Record<ClientFeatureFlagName, boolean> = {
  sso: false,
  clerk: false,
  analytics: false,
};

function readPublicEnvBool(name: string, defaultValue: boolean): boolean {
  const raw = process.env[name];
  if (raw === undefined || raw === '') return defaultValue;
  return raw === 'true' || raw === '1';
}

export function getClientFeatureDefaults(): Record<ClientFeatureFlagName, boolean> {
  return { ...DEFAULTS };
}

export function isClientFeatureEnabled(flag: ClientFeatureFlagName): boolean {
  if (flag === 'sso') {
    return readPublicEnvBool('NEXT_PUBLIC_FEATURE_SSO', DEFAULTS.sso);
  }
  if (flag === 'analytics') {
    return readPublicEnvBool('NEXT_PUBLIC_FEATURE_ADVANCED_ANALYTICS', DEFAULTS.analytics);
  }
  return DEFAULTS[flag] ?? false;
}

export function isProductFeatureEnabled(flag: ProductFeatureFlagName): boolean {
  switch (flag) {
    case 'aiAnalysis':
      return readPublicEnvBool('NEXT_PUBLIC_FEATURE_AI_ANALYSIS', true);
    case 'documentOcr':
      return readPublicEnvBool('NEXT_PUBLIC_FEATURE_DOCUMENT_OCR', false);
    case 'advancedAnalytics':
      return readPublicEnvBool('NEXT_PUBLIC_FEATURE_ADVANCED_ANALYTICS', false);
    default:
      return true;
  }
}
