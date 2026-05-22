/**
 * Feature Flags Configuration
 * Centralized control for feature enablement across environments
 */

import { env, isDev, isStaging, features } from '../env.js';

export type FeatureFlagName = 'ai_analysis' | 'document_ocr' | 'advanced_analytics' | 'webhooks' | 'api_access' | 'custom_domains' | 'sso';

export interface FeatureFlag {
  name: FeatureFlagName;
  description: string;
  enabled: boolean;
  environments: ('development' | 'staging' | 'production')[];
  rolloutPercentage?: number;
  dependencies?: string[];
}

const initialFlags: FeatureFlag[] = [
  {
    name: 'ai_analysis',
    description: 'AI-powered tender analysis and bid scoring',
    enabled: features.aiAnalysis,
    environments: ['development', 'staging', 'production'],
  },
  {
    name: 'document_ocr',
    description: 'Optical character recognition for document processing',
    enabled: features.documentOcr,
    environments: ['development', 'staging', 'production'],
  },
  {
    name: 'advanced_analytics',
    description: 'Advanced analytics and reporting dashboard',
    enabled: features.advancedAnalytics,
    environments: ['staging', 'production'],
  },
  {
    name: 'webhooks',
    description: 'Webhook notifications for tender events',
    enabled: features.webhooks,
    environments: ['development', 'staging', 'production'],
  },
  {
    name: 'api_access',
    description: 'REST API access for external integrations',
    enabled: features.apiAccess,
    environments: ['development', 'staging', 'production'],
  },
  {
    name: 'custom_domains',
    description: 'Custom domain support for organizations',
    enabled: features.customDomains,
    environments: ['production'],
  },
  {
    name: 'sso',
    description: 'Single sign-on with SAML/OIDC',
    enabled: features.sso,
    environments: ['staging', 'production'],
  },
];

let featureFlags: FeatureFlag[] = [...initialFlags];
let lastRefresh = Date.now();
const TTL_MS = 60_000;

function refreshFlags(): void {
  if (Date.now() - lastRefresh > TTL_MS) {
    featureFlags = [...initialFlags];
    lastRefresh = Date.now();
  }
}

function isFlagEnabledForRollout(flagName: string, percentage: number): boolean {
  let hash = 0;
  for (let i = 0; i < flagName.length; i++) {
    const char = flagName.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash |= 0;
  }
  return (Math.abs(hash) % 100) < percentage;
}

export function isFeatureAvailable(flagName: FeatureFlagName): boolean {
  refreshFlags();
  const flag = featureFlags.find((f) => f.name === flagName);

  if (!flag) {
    console.warn(`Unknown feature flag: ${flagName}`);
    return false;
  }

  const currentEnv = isDev ? 'development' : isStaging ? 'staging' : 'production';

  if (!flag.environments.includes(currentEnv)) {
    return false;
  }

  if (!flag.enabled) {
    return false;
  }

  if (flag.rolloutPercentage !== undefined) {
    return isFlagEnabledForRollout(flagName, flag.rolloutPercentage);
  }

  return true;
}

export function getEnabledFeatures(): FeatureFlag[] {
  refreshFlags();
  return featureFlags.filter((f) => isFeatureAvailable(f.name));
}

export function getAllFeatures(): FeatureFlag[] {
  refreshFlags();
  return featureFlags;
}