export interface QuotaStatus {
  resource: string;
  used: number;
  limit: number;
}

export interface UsageSummary {
  total_actions?: number;
  period_start?: string;
  period_end?: string;
}
