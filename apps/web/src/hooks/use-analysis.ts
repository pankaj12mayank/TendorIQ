import { useState, useCallback } from 'react';
import { useAnalysisStore } from '@/components/analysis/store';
import { TenderAnalysis, AnalysisSection } from '@/components/analysis/types';
import { MOCK_ANALYSIS } from '@/components/analysis/constants';

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
    setIsError(false);
    setError(null);
    
    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      setAnalysis(MOCK_ANALYSIS);
    } catch (err) {
      setIsError(true);
      setError('Failed to fetch analysis');
    }
  }, [setAnalysis]);

  const updateField = useCallback(async (
    section: AnalysisSection, 
    fieldId: string, 
    value: unknown
  ) => {
    await new Promise(resolve => setTimeout(resolve, 500));
    const store = useAnalysisStore.getState();
    store.updateSection(section, { [fieldId]: value });
  }, []);

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
    return analysis[section];
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