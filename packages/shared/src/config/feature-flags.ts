/**
 * Feature Flags Configuration
 * Centralized control for feature enablement across environments
 */

import { env, isDev, isProd, isStaging, features } from '../env.js';

export interface FeatureFlag {
  name: string;
  description: string;
  enabled: boolean;
  environments: ('development' | 'staging' | 'production')[];
  rolloutPercentage?: number;
  dependencies?: string[];
}

export const featureFlags: FeatureFlag[] = [
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

export function isFeatureAvailable(flagName: string): boolean {
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
    const random = Math.random() * 100;
    return random <= flag.rolloutPercentage;
  }

  return true;
}

export function getEnabledFeatures(): FeatureFlag[] {
  return featureFlags.filter((f) => isFeatureAvailable(f.name));
}

export function getAllFeatures(): FeatureFlag[] {
  return featureFlags;
}