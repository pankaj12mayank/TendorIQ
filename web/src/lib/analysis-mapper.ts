import {
  normalizeConfidencePercent,
  type AnalysisDashboardPayload,
} from '@/shared/analysis';

import type {
  TenderAnalysis,
  SummaryData,
  EligibilityData,
  TechnicalData,
  FinancialData,
  RisksData,
  DeadlinesData,
  MandatoryDocsData,
  ImportantClausesData,
  ConfidenceScore,
} from '@/components/analysis/types';

function confidenceFrom(raw: unknown): ConfidenceScore {
  const c = (raw && typeof raw === 'object' ? raw : {}) as Record<string, unknown>;
  const value = normalizeConfidencePercent(c.value);
  return {
    value,
    label: String(c.label ?? (value >= 80 ? 'High' : value >= 50 ? 'Medium' : 'Low')),
    factors: Array.isArray(c.factors) ? (c.factors as string[]) : [],
  };
}

function mapSummary(section: Record<string, unknown> | undefined, tenderId: string): SummaryData {
  const s = section ?? {};
  const highlights =
    (Array.isArray(s.keyHighlights) ? (s.keyHighlights as string[]) : null) ??
    (Array.isArray(s.keyFindings) ? (s.keyFindings as string[]) : []) ??
    [];
  return {
    title: String(s.title ?? 'Tender analysis'),
    referenceNumber: String(s.referenceNumber ?? tenderId.slice(0, 8)),
    organization: String(s.organization ?? '—'),
    category: String(s.category ?? 'General'),
    value: String(s.value ?? '—'),
    description: String(s.description ?? s.overallAssessment ?? ''),
    confidence: confidenceFrom(s.confidence),
    keyHighlights: highlights,
    concerns: Array.isArray(s.concerns) ? (s.concerns as string[]) : [],
  };
}

function mapEligibility(section: Record<string, unknown> | undefined): EligibilityData {
  const s = section ?? {};
  const rawCriteria = Array.isArray(s.criteria) ? s.criteria : [];
  const criteria = rawCriteria.map((row, idx) => {
    const c = (row && typeof row === 'object' ? row : {}) as Record<string, unknown>;
    const status = String(c.status ?? '').toLowerCase();
    const isMet =
      c.isMet === true || status === 'met' || status === 'pass'
        ? true
        : c.isMet === false || status === 'not_met' || status === 'fail'
          ? false
          : null;
    return {
      id: String(c.id ?? idx + 1),
      criterion: String(c.criterion ?? c.name ?? `Criterion ${idx + 1}`),
      requirement: String(c.requirement ?? c.details ?? ''),
      isMet,
      notes: c.notes ? String(c.notes) : undefined,
      confidence: Number(c.confidence ?? 0),
    };
  });
  const score = Number(s.overallScore ?? 0);
  return {
    overallScore: score,
    overallConfidence: confidenceFrom(s.overallConfidence ?? { value: score }),
    criteria,
    summary: String(s.summary ?? ''),
  };
}

function mapTechnical(section: Record<string, unknown> | undefined): TechnicalData {
  const s = section ?? {};
  const rawReqs = Array.isArray(s.requirements) ? s.requirements : [];
  const requirements = rawReqs.map((row, idx) => {
    const r = (row && typeof row === 'object' ? row : {}) as Record<string, unknown>;
    const status = String(r.status ?? '').toLowerCase();
    const isCompliant =
      r.isCompliant === true || status === 'compliant' || status === 'met'
        ? true
        : r.isCompliant === false || status === 'non_compliant'
          ? false
          : null;
    return {
      id: String(r.id ?? idx + 1),
      name: String(r.name ?? `Requirement ${idx + 1}`),
      specification: String(r.specification ?? r.details ?? ''),
      isCompliant,
      weight: Number(r.weight ?? 0),
      notes: r.notes ? String(r.notes) : undefined,
    };
  });
  const rate = Number(s.complianceRate ?? s.overallScore ?? 0);
  return {
    overallScore: rate,
    overallConfidence: confidenceFrom(s.overallConfidence ?? { value: rate }),
    requirements,
    complianceRate: rate,
    summary: String(s.summary ?? ''),
  };
}

function mapFinancial(section: Record<string, unknown> | undefined): FinancialData {
  const s = section ?? {};
  const total = s.totalValue;
  const currency = String(s.currency ?? 'USD');
  const totalStr =
    typeof total === 'number'
      ? new Intl.NumberFormat(undefined, { style: 'currency', currency }).format(total)
      : String(total ?? '—');
  const items = Array.isArray(s.items) ? s.items : Array.isArray(s.breakdown) ? s.breakdown : [];
  return {
    totalValue: totalStr,
    currency,
    breakdown: items.map((row) => {
      const i = (row && typeof row === 'object' ? row : {}) as Record<string, unknown>;
      return {
        item: String(i.item ?? i.name ?? 'Item'),
        amount: Number(i.amount ?? 0),
        unit: String(i.unit ?? ''),
        quantity: Number(i.quantity ?? 1),
        total: Number(i.total ?? i.amount ?? 0),
      };
    }),
    paymentTerms: String(s.paymentTerms ?? ''),
    advances: Array.isArray(s.advances) ? (s.advances as FinancialData['advances']) : [],
    overallConfidence: confidenceFrom(s.overallConfidence ?? { value: 0 }),
    summary: String(s.summary ?? ''),
  };
}

function mapRisks(section: Record<string, unknown> | undefined): RisksData {
  const s = section ?? {};
  const rawRisks = Array.isArray(s.risks) ? s.risks : [];
  const risks = rawRisks.map((row, idx) => {
    const r = (row && typeof row === 'object' ? row : {}) as Record<string, unknown>;
    const sev = String(r.severity ?? 'medium').toLowerCase();
    const severity =
      sev === 'low' || sev === 'high' || sev === 'critical' ? sev : ('medium' as const);
    return {
      id: String(r.id ?? idx + 1),
      title: String(r.title ?? `Risk ${idx + 1}`),
      description: String(r.description ?? ''),
      severity,
      probability: Number(r.probability ?? 0),
      impact: String(r.impact ?? ''),
      mitigation: String(r.mitigation ?? ''),
      owner: r.owner ? String(r.owner) : undefined,
    };
  });
  const score = Number(s.overallRiskScore ?? 0);
  return {
    overallRiskScore: score,
    risks,
    overallConfidence: confidenceFrom(s.overallConfidence ?? { value: 100 - score }),
    summary: String(s.summary ?? ''),
  };
}

function mapDeadlines(section: Record<string, unknown> | undefined): DeadlinesData {
  const s = section ?? {};
  const raw = Array.isArray(s.deadlines) ? s.deadlines : [];
  const deadlines = raw.map((row, idx) => {
    const d = (row && typeof row === 'object' ? row : {}) as Record<string, unknown>;
    const date = String(d.date ?? d.dueDate ?? '');
    return {
      id: String(d.id ?? idx + 1),
      name: String(d.name ?? d.title ?? `Deadline ${idx + 1}`),
      date,
      type: (d.type as DeadlinesData['deadlines'][0]['type']) ?? 'other',
      isMet: d.isMet === true ? true : d.isMet === false ? false : null,
      daysRemaining: Number(d.daysRemaining ?? 0),
      notes: d.notes ? String(d.notes) : undefined,
    };
  });
  return {
    deadlines,
    earliestDeadline: String(s.earliestDeadline ?? deadlines[0]?.date ?? ''),
    overallConfidence: confidenceFrom(s.overallConfidence ?? { value: 0 }),
    summary: String(s.summary ?? ''),
  };
}

function mapImportantClauses(section: Record<string, unknown> | undefined): ImportantClausesData {
  const s = section ?? {};
  const raw = Array.isArray(s.clauses) ? s.clauses : [];
  const clauses = raw.map((row, idx) => {
    const c = (row && typeof row === 'object' ? row : {}) as Record<string, unknown>;
    return {
      id: String(c.id ?? idx + 1),
      title: String(c.title ?? `Clause ${idx + 1}`),
      excerpt: String(c.excerpt ?? c.text ?? ''),
      impact: String(c.impact ?? ''),
      category: String(c.category ?? 'other'),
    };
  });
  return {
    clauses,
    summary: String(s.summary ?? ''),
  };
}

function mapMandatoryDocs(section: Record<string, unknown> | undefined): MandatoryDocsData {
  const s = section ?? {};
  const rawDocs = Array.isArray(s.documents) ? s.documents : [];
  const documents = rawDocs.map((row, idx) => {
    const d = (row && typeof row === 'object' ? row : {}) as Record<string, unknown>;
    const status = String(d.status ?? '').toLowerCase();
    const isSubmitted =
      d.isSubmitted === true || status === 'submitted' || status === 'complete'
        ? true
        : d.isSubmitted === false
          ? false
          : null;
    return {
      id: String(d.id ?? idx + 1),
      name: String(d.name ?? `Document ${idx + 1}`),
      description: String(d.description ?? ''),
      isRequired: d.isRequired !== false,
      isSubmitted,
      submittedDate: d.submittedDate ? String(d.submittedDate) : undefined,
      documentType: String(d.documentType ?? 'other'),
      pageLimit: d.pageLimit != null ? Number(d.pageLimit) : undefined,
      notes: d.notes ? String(d.notes) : undefined,
      confidence: Number(d.confidence ?? 0),
    };
  });
  const completion = Number(s.overallCompletion ?? 0);
  return {
    overallCompletion: completion,
    documents,
    overallConfidence: confidenceFrom(s.overallConfidence ?? { value: completion }),
    summary: String(s.summary ?? ''),
  };
}

const ANALYSIS_STATUS = new Set(['pending', 'in_progress', 'completed', 'failed']);

export function mapAnalysisDashboardToUi(payload: AnalysisDashboardPayload & { tenderId: string }): TenderAnalysis {
  const mandatory =
    (payload.mandatoryDocs as Record<string, unknown> | undefined) ??
    (payload.mandatory_docs as Record<string, unknown> | undefined);

  const statusRaw = String(payload.status ?? 'pending');
  const status = ANALYSIS_STATUS.has(statusRaw)
    ? (statusRaw as TenderAnalysis['status'])
    : 'pending';

  return {
    tenderId: payload.tenderId,
    status,
    summary: mapSummary(payload.summary as Record<string, unknown> | undefined, payload.tenderId),
    eligibility: mapEligibility(payload.eligibility as Record<string, unknown> | undefined),
    technical: mapTechnical(payload.technical as Record<string, unknown> | undefined),
    financial: mapFinancial(payload.financial as Record<string, unknown> | undefined),
    risks: mapRisks(payload.risks as Record<string, unknown> | undefined),
    deadlines: mapDeadlines(payload.deadlines as Record<string, unknown> | undefined),
    importantClauses: mapImportantClauses(
      payload.importantClauses as Record<string, unknown> | undefined
    ),
    mandatoryDocs: mapMandatoryDocs(mandatory),
    createdAt: String(payload.createdAt ?? payload.created_at ?? ''),
    updatedAt: String(payload.updatedAt ?? payload.updated_at ?? ''),
  };
}
