import { Request, Response, NextFunction } from 'express';

export interface PlanLimits {
  users: number | null;
  documents: number | null;
  apiCalls: number | null;
  storage: number | null;
  tenders: number | null;
  bids: number | null;
  aiAnalysis: number | null;
}

export interface PlanMiddlewareOptions {
  enforceQuota?: boolean;
  allowGracePeriod?: boolean;
}

const PLAN_LIMITS: Record<string, PlanLimits> = {
  free: {
    users: 2,
    documents: 50,
    apiCalls: 500,
    storage: 1,
    tenders: 10,
    bids: 25,
    aiAnalysis: 25,
  },
  pro: {
    users: 10,
    documents: 500,
    apiCalls: 5000,
    storage: 20,
    tenders: 100,
    bids: 250,
    aiAnalysis: 200,
  },
  enterprise: {
    users: null,
    documents: null,
    apiCalls: null,
    storage: 500,
    tenders: null,
    bids: null,
    aiAnalysis: null,
  },
};

export function planMiddleware(options: PlanMiddlewareOptions = {}) {
  const { enforceQuota = true, allowGracePeriod = true } = options;

  return async (req: Request, res: Response, next: NextFunction) => {
    try {
      const userId = req.headers['x-user-id'] as string;
      
      if (!userId) {
        return res.status(401).json({ error: 'Authentication required' });
      }

      const userPlan = (req.headers['x-user-plan'] as string) || 'free';
      const limits = PLAN_LIMITS[userPlan] || PLAN_LIMITS.free;

      (req as any).userPlan = userPlan;
      (req as any).planLimits = limits;

      if (enforceQuota) {
        const quotaCheck = await checkQuota(req, limits, allowGracePeriod);
        if (!quotaCheck.allowed) {
          return res.status(403).json({
            error: 'Quota exceeded',
            code: 'QUOTA_EXCEEDED',
            feature: quotaCheck.feature,
            used: quotaCheck.used,
            limit: quotaCheck.limit,
            message: `You have exceeded your ${quotaCheck.feature} limit. Please upgrade your plan.`,
            upgradeUrl: '/billing?upgrade=true',
          });
        }
      }

      next();
    } catch (error) {
      console.error('Plan middleware error:', error);
      next(error);
    }
  };
}

async function checkQuota(
  req: Request,
  limits: PlanLimits,
  allowGracePeriod: boolean
): Promise<{ allowed: boolean; feature?: string; used?: number; limit?: number }> {
  const featureKey = req.headers['x-quota-feature'] as string;
  
  if (!featureKey) {
    return { allowed: true };
  }

  const limitMap: Record<string, number | null> = {
    users: limits.users,
    documents: limits.documents,
    api_calls: limits.apiCalls,
    storage: limits.storage,
    tenders: limits.tenders,
    bids: limits.bids,
    ai_analysis: limits.aiAnalysis,
  };

  const limit = limitMap[featureKey];
  
  if (limit === null) {
    return { allowed: true };
  }

  const usageKey = `usage_${featureKey}`;
  const currentUsage = parseInt((req.headers[usageKey] as string) || '0', 10);
  const requestedAmount = parseInt((req.headers['x-quota-amount'] as string) || '1', 10);

  if (currentUsage + requestedAmount > limit) {
    return {
      allowed: false,
      feature: featureKey,
      used: currentUsage,
      limit,
    };
  }

  return { allowed: true };
}

export function requirePlan(requiredPlans: string[]) {
  return (req: Request, res: Response, next: NextFunction) => {
    const userPlan = (req as any).userPlan || 'free';

    if (!requiredPlans.includes(userPlan)) {
      return res.status(403).json({
        error: 'Plan requirement not met',
        code: 'PLAN_REQUIRED',
        requiredPlans,
        currentPlan: userPlan,
        message: `This feature requires one of: ${requiredPlans.join(', ')}`,
      });
    }

    next();
  };
}

export function requireFeature(feature: string, limitHeader: string = 'x-feature-limit') {
  return (req: Request, res: Response, next: NextFunction) => {
    const limits = (req as any).planLimits as PlanLimits;
    
    if (!limits) {
      return next();
    }

    const limitMap: Record<string, number | null> = {
      users: limits.users,
      documents: limits.documents,
      api_calls: limits.apiCalls,
      storage: limits.storage,
      tenders: limits.tenders,
      bids: limits.bids,
      ai_analysis: limits.aiAnalysis,
    };

    const limit = limitMap[feature];

    if (limit !== null) {
      const currentUsage = parseInt((req.headers[limitHeader] as string) || '0', 10);
      
      if (currentUsage >= limit) {
        return res.status(403).json({
          error: 'Feature limit reached',
          code: 'FEATURE_LIMIT_REACHED',
          feature,
          used: currentUsage,
          limit,
        });
      }
    }

    next();
  };
}

export const planRoutes = {
  free: [
    '/api/tenders',
    '/api/bids',
    '/api/documents',
  ],
  pro: [
    '/api/tenders',
    '/api/bids',
    '/api/documents',
    '/api/ai-analysis',
    '/api/analytics',
    '/api/templates',
  ],
  enterprise: [
    '/api/*',
  ],
};

export function getPlanFeatures(plan: string): string[] {
  const features: Record<string, string[]> = {
    free: ['basic_tenders', 'basic_bids', 'limited_docs', 'community_support'],
    pro: ['advanced_tenders', 'advanced_bids', 'unlimited_docs', 'ai_analysis', 'email_support', 'api_access'],
    enterprise: ['all_pro_features', 'priority_support', 'sso', 'custom_branding', 'dedicated_account_manager', 'custom_integrations'],
  };
  
  return features[plan] || features.free;
}

export function validatePlanChange(
  currentPlan: string,
  newPlan: string
): { valid: boolean; changeType: 'upgrade' | 'downgrade' | 'same'; proration?: number } {
  const planOrder = ['free', 'pro', 'enterprise'];
  const currentIndex = planOrder.indexOf(currentPlan);
  const newIndex = planOrder.indexOf(newPlan);

  if (currentIndex === newIndex) {
    return { valid: true, changeType: 'same' };
  }

  if (newIndex > currentIndex) {
    return { valid: true, changeType: 'upgrade' };
  }

  return { valid: true, changeType: 'downgrade' };
}

export function calculateProration(
  currentPlan: string,
  newPlan: string,
  daysRemaining: number,
  totalDays: number
): number {
  const prices: Record<string, number> = {
    free: 0,
    pro: 4900,
    enterprise: 19900,
  };

  const currentPrice = prices[currentPlan] || 0;
  const newPrice = prices[newPlan] || 0;
  const priceDiff = newPrice - currentPrice;
  
  const dailyRate = priceDiff / totalDays;
  return Math.round(dailyRate * daysRemaining);
}