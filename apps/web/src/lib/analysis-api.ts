import { api } from './api-client';
import { unwrapData } from './api-envelope';
import type { TenderAnalysis } from '@/components/analysis/types';

/** Load dashboard-shaped analysis for a tender (authenticated). */
export async function fetchTenderAnalysis(tenderId: string): Promise<unknown> {
  const raw = await api.get<{ data?: unknown }>(`/api/v1/analysis/tender/${tenderId}`);
  return unwrapData(raw);
}

export async function patchTenderAnalysisField(
  tenderId: string,
  body: { section: string; field_id: string; value: unknown }
): Promise<unknown> {
  const raw = await api.patch<{ data?: unknown }>(`/api/v1/analysis/tender/${tenderId}`, body);
  return unwrapData(raw);
}

export type { TenderAnalysis };
