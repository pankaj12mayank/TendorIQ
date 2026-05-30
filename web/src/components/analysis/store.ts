import { create } from 'zustand';
import { 
  TenderAnalysis, 
  AnalysisSection, 
  EditState,
  ExportOptions,
  ConfidenceScore 
} from './types';


interface AnalysisState {
  analysis: TenderAnalysis | null;
  activeSection: AnalysisSection;
  editState: EditState | null;
  isLoading: boolean;
  isSaving: boolean;
  hasUnsavedChanges: boolean;
  
  setAnalysis: (analysis: TenderAnalysis) => void;
  setActiveSection: (section: AnalysisSection) => void;
  startEdit: (section: AnalysisSection, fieldId: string, value: unknown) => void;
  updateEditValue: (value: unknown) => void;
  saveEdit: () => void;
  cancelEdit: () => void;
  updateSection: (section: AnalysisSection, data: unknown) => void;
  exportAnalysis: (options: ExportOptions) => Promise<void>;
  refreshAnalysis: (tenderId: string) => Promise<void>;
}

export const useAnalysisStore = create<AnalysisState>((set, get) => ({
  analysis: null,
  activeSection: 'summary',
  editState: null,
  isLoading: false,
  isSaving: false,
  hasUnsavedChanges: false,

  setAnalysis: (analysis) => set({ analysis }),

  setActiveSection: (section) => set({ activeSection: section }),

  startEdit: (section, fieldId, value) => 
    set({ editState: { section, fieldId, originalValue: value, newValue: value } }),

  updateEditValue: (value) =>
    set((state) => ({
      editState: state.editState ? { ...state.editState, newValue: value } : null,
      hasUnsavedChanges: true
    })),

  saveEdit: () => {
    const { editState, analysis } = get();
    if (!editState || !analysis || !editState.section || !editState.fieldId) return;

    set({ isSaving: true });

    const sectionKey = editState.section as string;
    const section = (analysis as unknown as Record<string, unknown>)[sectionKey] as Record<string, unknown> ?? {};
    const updatedAnalysis = {
      ...analysis,
      [sectionKey]: { ...section, [editState.fieldId]: editState.newValue },
    };
    
    set({
      analysis: updatedAnalysis as typeof analysis,
      editState: null,
      isSaving: false,
      hasUnsavedChanges: false
    });
  },

  cancelEdit: () => set({ editState: null }),

  updateSection: (section, data) => {
    const { analysis } = get();
    if (!analysis) return;

    const sectionKey = section as string;
    const currentSection = (analysis as unknown as Record<string, unknown>)[sectionKey] as Record<string, unknown> ?? {};
    
    set({ 
      analysis: { 
        ...analysis, 
        [sectionKey]: { ...currentSection, ...data as Record<string, unknown> },
        updatedAt: new Date().toISOString()
      },
      hasUnsavedChanges: true
    });
  },

  exportAnalysis: async (_options) => {
    const { analysis } = get();
    if (!analysis?.tenderId) return;

    set({ isLoading: true });
    try {
      const { downloadTenderAnalysisPdf } = await import('@/lib/export-lite');
      await downloadTenderAnalysisPdf(analysis.tenderId);
    } finally {
      set({ isLoading: false });
    }
  },

  refreshAnalysis: async (tenderId: string) => {
    if (!tenderId) return;
    set({ isLoading: true });
    try {
      const { fetchTenderAnalysis } = await import('@/lib/analysis-api');
      const data = await fetchTenderAnalysis(tenderId);
      set({ analysis: data as TenderAnalysis, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },
}));

export const formatConfidence = (confidence: ConfidenceScore): string => {
  return `${confidence.value}% - ${confidence.label}`;
};

export const getConfidenceColor = (value: number): string => {
  if (value >= 80) return 'text-green-600';
  if (value >= 60) return 'text-yellow-600';
  return 'text-red-600';
};

export const getRiskColor = (severity: string): string => {
  switch (severity) {
    case 'critical': return 'bg-red-100 text-red-800 border-red-200';
    case 'high': return 'bg-orange-100 text-orange-800 border-orange-200';
    case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    case 'low': return 'bg-green-100 text-green-800 border-green-200';
    default: return 'bg-gray-100 text-gray-800 border-gray-200';
  }
};

export const getStatusColor = (status: 'met' | 'not_met' | 'unknown'): string => {
  switch (status) {
    case 'met': return 'bg-green-100 text-green-800';
    case 'not_met': return 'bg-red-100 text-red-800';
    case 'unknown': return 'bg-gray-100 text-gray-800';
    default: return 'bg-gray-100 text-gray-800';
  }
};

const ANALYSIS_SECTIONS: { id: AnalysisSection; label: string }[] = [
  { id: 'summary', label: 'Summary' },
  { id: 'eligibility', label: 'Eligibility' },
  { id: 'technical', label: 'Technical' },
  { id: 'financial', label: 'Financial' },
  { id: 'risks', label: 'Risks' },
  { id: 'deadlines', label: 'Deadlines' },
  { id: 'important_clauses', label: 'Clauses' },
  { id: 'mandatory_docs', label: 'Documents' },
];

export function useAnalysisSections() {
  const activeSection = useAnalysisStore((s) => s.activeSection);
  const setActiveSection = useAnalysisStore((s) => s.setActiveSection);
  const analysis = useAnalysisStore((s) => s.analysis);

  const getSectionProgress = (section: AnalysisSection): number => {
    if (!analysis) return 0;
    switch (section) {
      case 'summary':
        return analysis.summary.confidence.value;
      case 'eligibility':
        return analysis.eligibility.overallScore;
      case 'technical':
        return analysis.technical.complianceRate;
      case 'financial':
        return 85;
      case 'risks':
        return 100 - analysis.risks.overallRiskScore;
      case 'deadlines':
        return analysis.deadlines.deadlines.length > 0 ? 90 : 0;
      case 'important_clauses':
        return analysis.importantClauses.clauses.length > 0 ? 88 : 0;
      case 'mandatory_docs':
        return analysis.mandatoryDocs.overallCompletion;
      default:
        return 0;
    }
  };

  return {
    activeSection,
    setActiveSection,
    sections: ANALYSIS_SECTIONS,
    getSectionProgress,
  };
}