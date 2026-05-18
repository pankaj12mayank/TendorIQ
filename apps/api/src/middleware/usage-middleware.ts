import { Request, Response, NextFunction } from 'express';
import { FeatureKey, QuotaCheckResult } from '../../types';

export interface UsageMiddlewareOptions {
  trackAll?: boolean;
  featureKey?: FeatureKey;
  costPerUnit?: number;
}

interface QuotaResult {
  allowed: boolean;
  currentUsage: number;
  limit: number | null;
  remaining: number | null;
  percentage: number;
}

const PLAN_LIMITS: Record<string, Record<FeatureKey, number | null>> = {
  free: {
    uploads: 50,
    storage: 1,
    ai_tokens: 1000,
    proposal_generations: 5,
    exports: 25,
    api_requests: 500,
    documents: 50,
    users: 2,
    tenders: 10,
    bids: 25,
    ai_analysis: 25,
    ocr_pages: 10,
  },
  pro: {
    uploads: 500,
    storage: 20,
    ai_tokens: 10000,
    proposal_generations: 100,
    exports: 500,
    api_requests: 5000,
    documents: 500,
    users: 10,
    tenders: 100,
    bids: 250,
    ai_analysis: 200,
    ocr_pages: 100,
  },
  enterprise: {
    uploads: null,
    storage: 500,
    ai_tokens: null,
    proposal_generations: null,
    exports: null,
    api_requests: null,
    documents: null,
    users: null,
    tenders: null,
    bids: null,
    ai_analysis: null,
    ocr_pages: null,
  },
};

export function usageTrackingMiddleware(options: UsageMiddlewareOptions = {}) {
  const { featureKey, trackAll = true } = options;

  return async (req: Request, res: Response, next: NextFunction) => {
    try {
      const userId = req.headers['x-user-id'] as string;
      const userPlan = (req.headers['x-user-plan'] as string) || 'free';
      const usageHeader = req.headers['x-usage-amount'] as string;
      const featureHeader = req.headers['x-feature-key'] as string;

      const targetFeature = (featureKey || featureHeader || 'api_requests') as FeatureKey;
      const amount = parseInt(usageHeader || '1', 10);

      if (!userId) {
        return next();
      }

      const limits = PLAN_LIMITS[userPlan] || PLAN_LIMITS.free;
      const limit = limits[targetFeature];

      (req as any).usageInfo = {
        featureKey: targetFeature,
        amount,
        limit,
        userPlan,
      };

      next();
    } catch (error) {
      console.error('Usage tracking middleware error:', error);
      next(error);
    }
  };
}

export function quotaEnforcementMiddleware(featureKey: FeatureKey, requiredAmount = 1) {
  return async (req: Request, res: Response, next: NextFunction) => {
    try {
      const userId = req.headers['x-user-id'] as string;
      const userPlan = (req.headers['x-user-plan'] as string) || 'free';
      const overrideHeader = req.headers['x-quota-override'] as string;

      if (!userId) {
        return res.status(401).json({ error: 'Authentication required' });
      }

      const limits = PLAN_LIMITS[userPlan] || PLAN_LIMITS.free;
      const limit = limits[featureKey];

      if (limit === null) {
        return next();
      }

      const currentUsage = parseInt((req.headers[`x-usage-${featureKey}`] as string) || '0', 10);
      const remaining = limit - currentUsage;

      if (overrideHeader === 'admin-bypass') {
        return next();
      }

      if (remaining < requiredAmount) {
        const percentage = (currentUsage / limit) * 100;
        
        return res.status(403).json({
          error: 'Quota exceeded',
          code: 'QUOTA_EXCEEDED',
          feature: featureKey,
          used: currentUsage,
          limit,
          remaining: Math.max(0, remaining),
          percentage: Math.round(percentage),
          message: `Quota limit reached for ${featureKey}. Please upgrade your plan.`,
          upgradeUrl: '/billing?upgrade=true',
          resetDate: getNextResetDate(featureKey),
        });
      }

      next();
    } catch (error) {
      console.error('Quota enforcement middleware error:', error);
      next(error);
    }
  };
}

export function getQuotaStatus(
  userPlan: string,
  featureKey: FeatureKey,
  currentUsage: number
): QuotaResult {
  const limits = PLAN_LIMITS[userPlan] || PLAN_LIMITS.free;
  const limit = limits[featureKey];

  if (limit === null) {
    return {
      allowed: true,
      currentUsage,
      limit: null,
      remaining: null,
      percentage: 0,
    };
  }

  const remaining = Math.max(0, limit - currentUsage);
  const percentage = (currentUsage / limit) * 100;

  return {
    allowed: remaining > 0,
    currentUsage,
    limit,
    remaining,
    percentage: Math.round(percentage * 100) / 100,
  };
}

export function checkAllQuotas(userPlan: string): Record<FeatureKey, QuotaResult> {
  const limits = PLAN_LIMITS[userPlan] || PLAN_LIMITS.free;
  const results: Record<string, QuotaResult> = {};

  (Object.keys(limits) as FeatureKey[]).forEach((key) => {
    results[key] = {
      allowed: true,
      currentUsage: 0,
      limit: limits[key],
      remaining: limits[key],
      percentage: 0,
    };
  });

  return results as Record<FeatureKey, QuotaResult>;
}

export function applyOverride(
  overrides: Record<string, number | null>,
  featureKey: FeatureKey,
  newLimit: number,
  expiresAt?: Date
): Record<string, number | null> {
  const updated = { ...overrides };
  updated[featureKey] = newLimit;
  return updated;
}

export function removeOverride(
  overrides: Record<string, number | null>,
  featureKey: FeatureKey
): Record<string, number | null> {
  const updated = { ...overrides };
  delete updated[featureKey];
  return updated;
}

export function getNextResetDate(featureKey: string): string {
  const now = new Date();
  
  switch (featureKey) {
    case 'api_requests':
    case 'uploads':
    case 'storage':
    case 'ai_tokens':
    case 'documents':
    case 'tenders':
    case 'bids':
    case 'ai_analysis':
    case 'ocr_pages':
    case 'proposal_generations':
    case 'exports':
      return new Date(now.getFullYear(), now.getMonth() + 1, 1).toISOString();
    case 'users':
      return 'never';
    default:
      return new Date(now.getFullYear(), now.getMonth() + 1, 1).toISOString();
  }
}

export function calculateCost(featureKey: FeatureKey, amount: number, userPlan: string): number {
  const costRates: Record<string, number> = {
    uploads: 0.01,
    storage: 0.10,
    ai_tokens: 0.001,
    proposal_generations: 0.50,
    exports: 0.05,
    api_requests: 0.0001,
    documents: 0,
    users: 0,
    tenders: 0,
    bids: 0,
    ai_analysis: 0.25,
    ocr_pages: 0.02,
  };

  const rate = costRates[featureKey] || 0;
  let cost = rate * amount;

  if (userPlan === 'pro') {
    cost *= 0.8;
  } else if (userPlan === 'enterprise') {
    cost *= 0.5;
  }

  return Math.round(cost * 100) / 100;
}

export const usageRoutes = {
  'POST /api/usage/track': {
    description: 'Track usage for a feature',
    params: ['featureKey', 'quantity'],
  },
  'GET /api/usage/quotas': {
    description: 'Get all quota statuses',
  },
  'GET /api/usage/quotas/:featureKey': {
    description: 'Get quota status for specific feature',
    params: ['featureKey'],
  },
  'GET /api/usage/alerts': {
    description: 'Get quota alerts',
  },
  'PATCH /api/usage/alerts/:alertId': {
    description: 'Update alert (read/dismiss)',
    params: ['alertId'],
  },
  'POST /api/usage/override': {
    description: 'Create admin override',
    params: ['userId', 'featureKey', 'newLimit', 'reason'],
  },
  'DELETE /api/usage/override/:overrideId': {
    description: 'Revoke admin override',
    params: ['overrideId'],
  },
};