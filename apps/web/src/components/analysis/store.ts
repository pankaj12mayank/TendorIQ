import { create } from 'zustand';
import { 
  TenderAnalysis, 
  AnalysisSection, 
  EditState,
  ExportOptions,
  ConfidenceScore 
} from './types';
import { MOCK_ANALYSIS } from './constants';

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
  refreshAnalysis: () => Promise<void>;
}

export const useAnalysisStore = create<AnalysisState>((set, get) => ({
  analysis: MOCK_ANALYSIS,
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
    if (!editState || !analysis) return;

    set({ isSaving: true });
    
    setTimeout(() => {
      const updatedAnalysis = { ...analysis };
      (updatedAnalysis as Record<string, unknown>)[editState.section] = {
        ...(updatedAnalysis as Record<string, unknown>)[editState.section] as object,
        [editState.fieldId]: editState.newValue
      };
      
      set({
        analysis: updatedAnalysis,
        editState: null,
        isSaving: false,
        hasUnsavedChanges: false
      });
    }, 500);
  },

  cancelEdit: () => set({ editState: null }),

  updateSection: (section, data) => {
    const { analysis } = get();
    if (!analysis) return;
    
    set({ 
      analysis: { 
        ...analysis, 
        [section]: { ...(analysis as Record<string, unknown>)[section] as object, ...data as object },
        updatedAt: new Date().toISOString()
      },
      hasUnsavedChanges: true
    });
  },

  exportAnalysis: async (options) => {
    const { analysis } = get();
    if (!analysis) return;

    set({ isLoading: true });

    await new Promise(resolve => setTimeout(resolve, 1000));

    const sectionsToExport = Object.fromEntries(
      Object.entries(analysis).filter(([key]) => 
        options.includeSections.includes(key as AnalysisSection)
      )
    );

    const exportData = options.includeMetadata ? {
      metadata: {
        tenderId: analysis.tenderId,
        exportedAt: new Date().toISOString(),
        format: options.format
      },
      ...sectionsToExport
    } : sectionsToExport;

    const blob = new Blob(
      [options.format === 'json' ? JSON.stringify(exportData, null, 2) : JSON.stringify(exportData)],
      { type: 'application/json' }
    );
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `tender-analysis-${analysis.tenderId}.${options.format}`;
    a.click();
    URL.revokeObjectURL(url);

    set({ isLoading: false });
  },

  refreshAnalysis: async () => {
    set({ isLoading: true });
    await new Promise(resolve => setTimeout(resolve, 1500));
    set({ analysis: MOCK_ANALYSIS, isLoading: false });
  }
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