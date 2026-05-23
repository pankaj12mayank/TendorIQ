import { FeatureKey, AlertThreshold, QuotaStatus, UsageSummary, QuotaAlert } from './types';

export const FEATURE_CONFIG: Record<FeatureKey, {
  name: string;
  unit: string;
  description: string;
  costPerUnit?: number;
  icon?: string;
}> = {
  uploads: { name: 'File Uploads', unit: 'files', description: 'Document uploads', costPerUnit: 0.01 },
  storage: { name: 'Storage', unit: 'GB', description: 'Cloud storage used', costPerUnit: 0.10 },
  ai_tokens: { name: 'AI Tokens', unit: 'tokens', description: 'AI processing tokens' },
  proposal_generations: { name: 'Proposal Generation', unit: 'generations', description: 'AI proposal creations', costPerUnit: 0.50 },
  exports: { name: 'Exports', unit: 'exports', description: 'Document exports', costPerUnit: 0.05 },
  api_requests: { name: 'API Requests', unit: 'requests', description: 'API calls made' },
  documents: { name: 'Documents', unit: 'documents', description: 'Documents stored' },
  users: { name: 'Team Members', unit: 'users', description: 'User seats' },
  tenders: { name: 'Tenders', unit: 'tenders', description: 'Tender submissions' },
  bids: { name: 'Bids', unit: 'bids', description: 'Bid submissions' },
  ai_analysis: { name: 'AI Analysis', unit: 'analyses', description: 'AI document analysis', costPerUnit: 0.25 },
  ocr_pages: { name: 'OCR Pages', unit: 'pages', description: 'Pages processed with OCR', costPerUnit: 0.02 },
};

export const ALERT_THRESHOLDS: AlertThreshold[] = [
  { featureKey: 'uploads', warningPercent: 70, criticalPercent: 85, exceededPercent: 100 },
  { featureKey: 'storage', warningPercent: 75, criticalPercent: 90, exceededPercent: 100 },
  { featureKey: 'ai_tokens', warningPercent: 80, criticalPercent: 95, exceededPercent: 100 },
  { featureKey: 'proposal_generations', warningPercent: 75, criticalPercent: 90, exceededPercent: 100 },
  { featureKey: 'exports', warningPercent: 70, criticalPercent: 85, exceededPercent: 100 },
  { featureKey: 'api_requests', warningPercent: 80, criticalPercent: 95, exceededPercent: 100 },
  { featureKey: 'documents', warningPercent: 75, criticalPercent: 90, exceededPercent: 100 },
  { featureKey: 'users', warningPercent: 80, criticalPercent: 90, exceededPercent: 100 },
  { featureKey: 'tenders', warningPercent: 70, criticalPercent: 85, exceededPercent: 100 },
  { featureKey: 'bids', warningPercent: 70, criticalPercent: 85, exceededPercent: 100 },
  { featureKey: 'ai_analysis', warningPercent: 75, criticalPercent: 90, exceededPercent: 100 },
  { featureKey: 'ocr_pages', warningPercent: 70, criticalPercent: 85, exceededPercent: 100 },
];

export const MOCK_QUOTA_STATUS: QuotaStatus[] = [
  { featureKey: 'uploads', featureName: 'File Uploads', limit: 50, used: 32, remaining: 18, percentage: 64, isUnlimited: false, isExceeded: false, resetPeriod: 'monthly', nextResetAt: '2026-06-01' },
  { featureKey: 'storage', featureName: 'Storage', limit: 5, used: 2.3, remaining: 2.7, percentage: 46, isUnlimited: false, isExceeded: false, resetPeriod: 'monthly', nextResetAt: '2026-06-01', alertLevel: 'warning' },
  { featureKey: 'ai_tokens', featureName: 'AI Tokens', limit: 10000, used: 7850, remaining: 2150, percentage: 78.5, isUnlimited: false, isExceeded: false, resetPeriod: 'monthly', nextResetAt: '2026-06-01', alertLevel: 'warning' },
  { featureKey: 'proposal_generations', featureName: 'Proposal Generation', limit: 25, used: 18, remaining: 7, percentage: 72, isUnlimited: false, isExceeded: false, resetPeriod: 'monthly', nextResetAt: '2026-06-01', alertLevel: 'warning' },
  { featureKey: 'exports', featureName: 'Exports', limit: 100, used: 45, remaining: 55, percentage: 45, isUnlimited: false, isExceeded: false, resetPeriod: 'monthly', nextResetAt: '2026-06-01' },
  { featureKey: 'api_requests', featureName: 'API Requests', limit: 5000, used: 3240, remaining: 1760, percentage: 64.8, isUnlimited: false, isExceeded: false, resetPeriod: 'monthly', nextResetAt: '2026-06-01' },
  { featureKey: 'documents', featureName: 'Documents', limit: 500, used: 234, remaining: 266, percentage: 46.8, isUnlimited: false, isExceeded: false, resetPeriod: 'monthly', nextResetAt: '2026-06-01' },
  { featureKey: 'users', featureName: 'Team Members', limit: 10, used: 5, remaining: 5, percentage: 50, isUnlimited: false, isExceeded: false, resetPeriod: 'never' },
  { featureKey: 'tenders', featureName: 'Tenders', limit: 100, used: 45, remaining: 55, percentage: 45, isUnlimited: false, isExceeded: false, resetPeriod: 'monthly', nextResetAt: '2026-06-01' },
  { featureKey: 'bids', featureName: 'Bids', limit: 250, used: 89, remaining: 161, percentage: 35.6, isUnlimited: false, isExceeded: false, resetPeriod: 'monthly', nextResetAt: '2026-06-01' },
  { featureKey: 'ai_analysis', featureName: 'AI Analysis', limit: 200, used: 156, remaining: 44, percentage: 78, isUnlimited: false, isExceeded: false, resetPeriod: 'monthly', nextResetAt: '2026-06-01', alertLevel: 'critical' },
  { featureKey: 'ocr_pages', featureName: 'OCR Pages', limit: 100, used: 67, remaining: 33, percentage: 67, isUnlimited: false, isExceeded: false, resetPeriod: 'monthly', nextResetAt: '2026-06-01' },
];

export const MOCK_ALERTS: QuotaAlert[] = [
  { id: 'alert-1', userId: 'user-123', featureKey: 'ai_analysis', alertType: 'critical', thresholdPercent: 90, currentPercent: 78, isRead: false, isDismissed: false, createdAt: '2026-05-18T10:00:00Z' },
  { id: 'alert-2', userId: 'user-123', featureKey: 'storage', alertType: 'warning', thresholdPercent: 70, currentPercent: 46, isRead: false, isDismissed: false, createdAt: '2026-05-17T15:30:00Z' },
  { id: 'alert-3', userId: 'user-123', featureKey: 'ai_tokens', alertType: 'warning', thresholdPercent: 70, currentPercent: 78.5, isRead: true, isDismissed: false, createdAt: '2026-05-16T09:00:00Z' },
];

export const MOCK_USAGE_SUMMARY: UsageSummary = {
  totalUsage: 12547,
  totalCost: 156.78,
  periodStart: '2026-05-01',
  periodEnd: '2026-05-31',
  breakdown: [
    { featureKey: 'ai_tokens', featureName: 'AI Tokens', count: 7850, cost: 0, percentage: 62.6 },
    { featureKey: 'api_requests', featureName: 'API Requests', count: 3240, cost: 0, percentage: 25.8 },
    { featureKey: 'ai_analysis', featureName: 'AI Analysis', count: 156, cost: 39.00, percentage: 1.2 },
    { featureKey: 'ocr_pages', featureName: 'OCR Pages', count: 67, cost: 1.34, percentage: 0.5 },
    { featureKey: 'proposal_generations', featureName: 'Proposal Generation', count: 18, cost: 9.00, percentage: 0.1 },
    { featureKey: 'exports', featureName: 'Exports', count: 45, cost: 2.25, percentage: 0.4 },
    { featureKey: 'uploads', featureName: 'File Uploads', count: 32, cost: 0.32, percentage: 0.3 },
    { featureKey: 'storage', featureName: 'Storage', count: 2.3, cost: 0.23, percentage: 0.1 },
    { featureKey: 'documents', featureName: 'Documents', count: 234, cost: 0, percentage: 1.9 },
    { featureKey: 'tenders', featureName: 'Tenders', count: 45, cost: 0, percentage: 0.4 },
    { featureKey: 'bids', featureName: 'Bids', count: 89, cost: 0, percentage: 0.7 },
    { featureKey: 'users', featureName: 'Team Members', count: 5, cost: 0, percentage: 0.0 },
  ],
};

export const ALERT_COLORS = {
  warning: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  critical: 'bg-orange-100 text-orange-800 border-orange-200',
  exceeded: 'bg-red-100 text-red-800 border-red-200',
};

export const FEATURE_ICONS: Record<FeatureKey, string> = {
  uploads: 'Upload',
  storage: 'HardDrive',
  ai_tokens: 'Cpu',
  proposal_generations: 'FileText',
  exports: 'Download',
  api_requests: 'Zap',
  documents: 'File',
  users: 'Users',
  tenders: 'Briefcase',
  bids: 'TrendingUp',
  ai_analysis: 'Brain',
  ocr_pages: 'Scan',
};

export const TRACKED_FEATURES: FeatureKey[] = [
  'uploads',
  'storage',
  'ai_tokens',
  'proposal_generations',
  'exports',
  'api_requests',
  'documents',
  'users',
  'tenders',
  'bids',
  'ai_analysis',
  'ocr_pages',
];

export const FEATURE_CATEGORIES = {
  'Documents & Storage': ['uploads', 'storage', 'documents', 'exports'] as FeatureKey[],
  'AI & Analysis': ['ai_tokens', 'ai_analysis', 'ocr_pages', 'proposal_generations'] as FeatureKey[],
  'Business': ['tenders', 'bids'] as FeatureKey[],
  'Team': ['users', 'api_requests'] as FeatureKey[],
};

export function getAlertLevel(percentage: number): 'none' | 'warning' | 'critical' | 'exceeded' {
  if (percentage >= 100) return 'exceeded';
  if (percentage >= 85) return 'critical';
  if (percentage >= 70) return 'warning';
  return 'none';
}

/** Prefer API-provided feature name; fall back to static config. */
export function featureDisplayName(featureKey: FeatureKey, apiName?: string): string {
  if (apiName?.trim()) return apiName;
  return FEATURE_CONFIG[featureKey]?.name ?? featureKey;
}

export function mergeFeatureConfigFromQuotas(quotas: { featureKey: FeatureKey; featureName: string }[]): void {
  for (const q of quotas) {
    if (FEATURE_CONFIG[q.featureKey]) {
      FEATURE_CONFIG[q.featureKey] = {
        ...FEATURE_CONFIG[q.featureKey],
        name: q.featureName,
      };
    }
  }
}

export function formatUsage(count: number, unit: string): string {
  if (count >= 1000000) return `${(count / 1000000).toFixed(1)}M ${unit}`;
  if (count >= 1000) return `${(count / 1000).toFixed(1)}K ${unit}`;
  if (unit === 'GB' && count < 10) return `${count.toFixed(1)} ${unit}`;
  return `${Math.round(count)} ${unit}`;
}