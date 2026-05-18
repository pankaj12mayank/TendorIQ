import { useCallback, useState } from 'react';
import { useReviewStore } from '@/components/review/store';
import { 
  ReviewSession, 
  ReviewSection, 
  EditFieldPayload, 
  ApprovalAction,
  ReviewComment,
  AuditEntry,
  ChangeRecord,
  SectionStatus
} from '@/components/review/types';
import { MOCK_REVIEW_SESSION } from '@/components/review/constants';

interface UseReviewApiReturn {
  session: ReviewSession | null;
  isLoading: boolean;
  isError: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  submitApproval: (action: ApprovalAction, comments?: string) => Promise<void>;
  requestChanges: (sections: string[], comments: string) => Promise<void>;
  regenerateSection: (section: ReviewSection, reason: string) => Promise<void>;
  getSectionData: (section: ReviewSection) => unknown;
  getSectionStatus: (section: ReviewSection) => SectionStatus | undefined;
  getComments: (section?: ReviewSection) => ReviewComment[];
  getAuditLog: () => AuditEntry[];
  getChanges: () => ChangeRecord[];
}

export function useReviewApi(tenderId?: string): UseReviewApiReturn {
  const { session, isLoading, setSession, submitApproval: storeSubmitApproval, requestChanges: storeRequestChanges } = useReviewStore();
  const [isError, setIsError] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    setIsError(false);
    setError(null);
    
    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      setSession(MOCK_REVIEW_SESSION);
    } catch (err) {
      setIsError(true);
      setError('Failed to fetch review session');
    }
  }, [setSession]);

  const submitApproval = useCallback(async (action: ApprovalAction, comments?: string) => {
    await storeSubmitApproval(action, comments);
  }, [storeSubmitApproval]);

  const requestChanges = useCallback(async (sections: string[], comments: string) => {
    await storeRequestChanges(sections, comments);
  }, [storeRequestChanges]);

  const regenerateSection = useCallback(async (section: ReviewSection, reason: string) => {
    const store = useReviewStore.getState();
    await store.regenerateSection({
      section,
      reason,
      includeChanges: true,
      priority: 'normal',
    });
  }, []);

  const getSectionData = useCallback((section: ReviewSection): unknown => {
    if (!session) return null;
    
    switch (section) {
      case 'summary':
        return { title: 'IT Infrastructure Modernization', reference: 'IIT-2026-001' };
      case 'eligibility':
        return { criteria: [] };
      case 'technical':
        return { requirements: [] };
      case 'financial':
        return { totalValue: '$2,500,000' };
      case 'risks':
        return { risks: [] };
      case 'deadlines':
        return { deadlines: [] };
      case 'mandatory_docs':
        return { documents: [] };
      default:
        return null;
    }
  }, [session]);

  const getSectionStatus = useCallback((section: ReviewSection): SectionStatus | undefined => {
    return session?.sectionStatuses.find(s => s.section === section);
  }, [session]);

  const getComments = useCallback((section?: ReviewSection): ReviewComment[] => {
    if (!session) return [];
    if (!section) return session.comments;
    return session.comments.filter(c => c.section === section);
  }, [session]);

  const getAuditLog = useCallback((): AuditEntry[] => {
    return session?.auditLog || [];
  }, [session]);

  const getChanges = useCallback((): ChangeRecord[] => {
    return session?.changes || [];
  }, [session]);

  return {
    session,
    isLoading,
    isError,
    error,
    refetch,
    submitApproval,
    requestChanges,
    regenerateSection,
    getSectionData,
    getSectionStatus,
    getComments,
    getAuditLog,
    getChanges,
  };
}

interface UseReviewSectionsReturn {
  selectedSection: ReviewSection;
  setSelectedSection: (section: ReviewSection) => void;
  sections: readonly { id: ReviewSection; label: string; icon: string }[];
  getSectionStatus: (section: ReviewSection) => SectionStatus | undefined;
  getSectionProgress: (section: ReviewSection) => number;
}

export function useReviewSections(): UseReviewSectionsReturn {
  const { selectedSection, setSelectedSection, session } = useReviewStore();
  
  const sections = [
    { id: 'summary' as ReviewSection, label: 'Summary', icon: 'file-text' },
    { id: 'eligibility' as ReviewSection, label: 'Eligibility', icon: 'check-circle' },
    { id: 'technical' as ReviewSection, label: 'Technical', icon: 'cpu' },
    { id: 'financial' as ReviewSection, label: 'Financial', icon: 'dollar-sign' },
    { id: 'risks' as ReviewSection, label: 'Risks', icon: 'alert-triangle' },
    { id: 'deadlines' as ReviewSection, label: 'Deadlines', icon: 'clock' },
    { id: 'mandatory_docs' as ReviewSection, label: 'Documents', icon: 'folder' },
  ];

  const getSectionStatus = (section: ReviewSection): SectionStatus | undefined => {
    return session?.sectionStatuses.find(s => s.section === section);
  };

  const getSectionProgress = (section: ReviewSection): number => {
    const status = getSectionStatus(section);
    if (!status) return 0;
    
    if (status.approvalStatus === 'approved') return 100;
    if (status.approvalStatus === 'rejected') return 0;
    if (status.hasChanges) return 75;
    return 50;
  };

  return {
    selectedSection,
    setSelectedSection,
    sections,
    getSectionStatus,
    getSectionProgress,
  };
}

interface UseEditWorkflowReturn {
  editState: {
    section: ReviewSection | null;
    field: string | null;
    isEditing: boolean;
    originalValue: unknown;
    currentValue: unknown;
  };
  startEdit: (section: ReviewSection, field: string, value: unknown) => void;
  updateEditValue: (value: unknown) => void;
  saveEdit: () => Promise<void>;
  cancelEdit: () => void;
  isSaving: boolean;
}

export function useEditWorkflow(): UseEditWorkflowReturn {
  const { editState, startEdit, updateEditValue, saveEdit, cancelEdit, isSaving } = useReviewStore();
  
  return {
    editState,
    startEdit,
    updateEditValue,
    saveEdit,
    cancelEdit,
    isSaving,
  };
}

interface UseApprovalWorkflowReturn {
  workflow: ReviewSession['workflow'] | null;
  isLoading: boolean;
  submitApproval: (action: ApprovalAction, comments?: string) => Promise<void>;
  requestChanges: (sections: string[], comments: string) => Promise<void>;
  canApprove: boolean;
  currentStepName: string;
}

export function useApprovalWorkflow(): UseApprovalWorkflowReturn {
  const { session, isLoading, submitApproval, requestChanges } = useReviewApi();
  
  return {
    workflow: session?.workflow || null,
    isLoading,
    submitApproval,
    requestChanges,
    canApprove: true,
    currentStepName: session?.workflow.steps.find(s => s.status === 'in_progress')?.name || 'Unknown',
  };
}