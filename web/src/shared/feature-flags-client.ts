/** Lite feature flags — client-safe defaults. */

export type ClientFeatureFlagName = 'sso' | 'clerk' | 'analytics';

const DEFAULTS: Record<ClientFeatureFlagName, boolean> = {
  sso: false,
  clerk: false,
  analytics: false,
};

export function getClientFeatureDefaults(): Record<ClientFeatureFlagName, boolean> {
  return { ...DEFAULTS };
}

export function isClientFeatureEnabled(flag: ClientFeatureFlagName): boolean {
  return DEFAULTS[flag] ?? false;
}
