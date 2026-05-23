import { useState, useCallback, useEffect } from 'react';
import { z } from 'zod';
import { fetchTenderAnalysis, patchTenderAnalysisField } from '@/lib/analysis-api';
import { useAnalysisStore } from '@/components/analysis/store';
import { TenderAnalysis, AnalysisSection } from '@/components/analysis/types';

const analysisSchema = z.object({
  tenderId: z.string(),
  summary: z.object({
    confidence: z.object({ value: z.number(), label: z.string() }),
    keyFindings: z.array(z.string()),
    overallAssessment: z.string(),
  }),
  eligibility: z.object({
    overallScore: z.number(),
    criteria: z.array(z.object({ name: z.string(), status: z.string(), details: z.string() })),
  }),
  technical: z.object({
    complianceRate: z.number(),
    requirements: z.array(z.object({ id: z.string(), name: z.string(), status: z.string() })),
  }),
  financial: z.object({
    totalValue: z.number(),
    currency: z.string(),
    items: z.array(z.any()),
  }),
  risks: z.object({
    overallRiskScore: z.number(),
    risks: z.array(z.object({ id: z.string(), title: z.string(), severity: z.string(), description: z.string() })),
  }),
  deadlines: z.object({
    deadlines: z.array(z.object({ id: z.string(), title: z.string(), dueDate: z.string(), priority: z.string() })),
  }),
  mandatoryDocs: z.object({
    overallCompletion: z.number(),
    documents: z.array(z.object({ id: z.string(), name: z.string(), status: z.string() })),
  }),
  createdAt: z.string().optional().nullable(),
  updatedAt: z.string().optional().nullable(),
});

interface UseAnalysisApiReturn {
  analysis: TenderAnalysis | null;
  isLoading: boolean;
  isError: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  updateField: (section: AnalysisSection, fieldId: string, value: unknown) => Promise<void>;
  exportAnalysis: (format: 'pdf' | 'docx' | 'json' | 'csv') => Promise<void>;
  getSectionData: (section: AnalysisSection) => unknown;
}

export function useAnalysisApi(tenderId?: string): UseAnalysisApiReturn {
  const { analysis, isLoading, setAnalysis } = useAnalysisStore();
  const [isError, setIsError] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    if (!tenderId) {
      setIsError(true);
      setError('Missing tender ID');
      return;
    }
    setIsError(false);
    setError(null);
    useAnalysisStore.setState({ isLoading: true });

    try {
      const raw = await fetchTenderAnalysis(tenderId);
      setAnalysis(analysisSchema.parse(raw));
    } catch (err) {
      setIsError(true);
      setError('Failed to fetch analysis');
    } finally {
      useAnalysisStore.setState({ isLoading: false });
    }
  }, [setAnalysis, tenderId]);

  useEffect(() => {
    if (tenderId) {
      void refetch();
    }
  }, [tenderId, refetch]);

  const updateField = useCallback(async (
    section: AnalysisSection, 
    fieldId: string, 
    value: unknown
  ) => {
    try {
      await patchTenderAnalysisField(tenderId, {
        section,
        field_id: fieldId,
        value,
      });
      const store = useAnalysisStore.getState();
      store.updateSection(section, { [fieldId]: value });
    } catch (err) {
      setIsError(true);
      setError(err instanceof Error ? err.message : 'Failed to update field');
    }
  }, [tenderId]);

  const exportAnalysis = useCallback(async (format: 'pdf' | 'docx' | 'json' | 'csv') => {
    const store = useAnalysisStore.getState();
    await store.exportAnalysis({
      format,
      includeSections: ['summary', 'eligibility', 'technical', 'financial', 'risks', 'deadlines', 'mandatory_docs'],
      includeMetadata: true,
      includeConfidence: true
    });
  }, []);

  const getSectionData = useCallback((section: AnalysisSection): unknown => {
    if (!analysis) return null;
    return (analysis as unknown as Record<string, unknown>)[section as string];
  }, [analysis]);

  return {
    analysis,
    isLoading,
    isError,
    error,
    refetch,
    updateField,
    exportAnalysis,
    getSectionData
  };
}

interface UseAnalysisSectionsReturn {
  activeSection: AnalysisSection;
  setActiveSection: (section: AnalysisSection) => void;
  sections: readonly { id: AnalysisSection; label: string; icon: string }[];
  getSectionProgress: (section: AnalysisSection) => number;
}

export function useAnalysisSections(): UseAnalysisSectionsReturn {
  const { activeSection, setActiveSection, analysis } = useAnalysisStore();
  
  const sections = [
    { id: 'summary' as AnalysisSection, label: 'Summary', icon: 'file-text' },
    { id: 'eligibility' as AnalysisSection, label: 'Eligibility', icon: 'check-circle' },
    { id: 'technical' as AnalysisSection, label: 'Technical', icon: 'cpu' },
    { id: 'financial' as AnalysisSection, label: 'Financial', icon: 'dollar-sign' },
    { id: 'risks' as AnalysisSection, label: 'Risks', icon: 'alert-triangle' },
    { id: 'deadlines' as AnalysisSection, label: 'Deadlines', icon: 'clock' },
    { id: 'mandatory_docs' as AnalysisSection, label: 'Documents', icon: 'folder' }
  ];

  const getSectionProgress = (section: AnalysisSection): number => {
    if (!analysis) return 0;
    
    switch (section) {
      case 'eligibility':
        return analysis.eligibility.overallScore;
      case 'technical':
        return analysis.technical.complianceRate;
      case 'mandatory_docs':
        return analysis.mandatoryDocs.overallCompletion;
      case 'risks':
        return 100 - analysis.risks.overallRiskScore;
      default:
        return analysis.summary.confidence.value;
    }
  };

  return {
    activeSection,
    setActiveSection,
    sections,
    getSectionProgress
  };
}