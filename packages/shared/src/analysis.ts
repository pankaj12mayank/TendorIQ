/**
 * Tender analysis dashboard payload (loose API JSON → validated object).
 * UI view-model mapping lives in apps/web `analysis-mapper.ts`.
 */

import { z } from 'zod';

const looseRecord = z.record(z.unknown()).optional();

export const analysisDashboardSchema = z
  .object({
    tenderId: z.string().optional(),
    tender_id: z.string().optional(),
    status: z.string().optional(),
    summary: looseRecord,
    eligibility: looseRecord,
    technical: looseRecord,
    financial: looseRecord,
    risks: looseRecord,
    deadlines: looseRecord,
    mandatoryDocs: looseRecord,
    mandatory_docs: looseRecord,
    createdAt: z.union([z.string(), z.null()]).optional(),
    created_at: z.union([z.string(), z.null()]).optional(),
    updatedAt: z.union([z.string(), z.null()]).optional(),
    updated_at: z.union([z.string(), z.null()]).optional(),
  })
  .passthrough();

export type AnalysisDashboardPayload = z.infer<typeof analysisDashboardSchema>;

export function parseAnalysisDashboard(
  raw: unknown,
  fallbackTenderId: string
): AnalysisDashboardPayload & { tenderId: string } {
  const parsed = analysisDashboardSchema.parse(raw ?? {});
  const tenderId = parsed.tenderId ?? parsed.tender_id ?? fallbackTenderId;
  return { ...parsed, tenderId };
}

/** Normalize API confidence (0–1 float or 0–100) to UI percent. */
export function normalizeConfidencePercent(value: unknown): number {
  const n = Number(value);
  if (Number.isNaN(n)) return 0;
  if (n > 0 && n <= 1) return Math.round(n * 100);
  return Math.round(n);
}
