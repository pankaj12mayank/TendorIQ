import { useCallback, useState } from 'react';
import { api } from '@/lib/api-client';
import { useReviewStore } from '@/components/review/store';
import { 
  ReviewSession, 
  ReviewSection, 
  ApprovalAction,
  ReviewComment,
  AuditEntry,
  ChangeRecord,
  SectionStatus
} from '@/components/review/types';

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
      const res = await api.get<ReviewSession>(`/api/v1/review/session/${tenderId}`);
      setSession(res);
    } catch (err) {
      setIsError(true);
      setError('Failed to fetch review session');
    }
  }, [setSession, tenderId]);

  const submitApproval = useCallback(async (action: ApprovalAction, comments?: string) => {
    setIsError(false);
    setError(null);
    try {
      const res = await api.post<ReviewSession>(`/api/v1/review/session/${tenderId}/approval`, { action, comments });
      setSession(res);
    } catch (err) {
      setIsError(true);
      setError('Failed to submit approval');
    }
  }, [setSession, tenderId]);

  const requestChanges = useCallback(async (sections: string[], comments: string) => {
    setIsError(false);
    setError(null);
    try {
      const res = await api.post<ReviewSession>(`/api/v1/review/session/${tenderId}/request-changes`, { sections, comments });
      setSession(res);
    } catch (err) {
      setIsError(true);
      setError('Failed to request changes');
    }
  }, [setSession, tenderId]);

  const regenerateSection = useCallback(async (section: ReviewSection, reason: string) => {
    try {
      const res = await api.post<{ success: boolean }>(`/api/v1/review/session/${tenderId}/regenerate`, {
        section,
        reason,
        includeChanges: true,
        priority: 'normal',
      });
      if (res.success) {
        await refetch();
      }
    } catch (err) {
      setIsError(true);
      setError('Failed to regenerate section');
    }
  }, [tenderId, refetch]);

  const getSectionData = useCallback((section: ReviewSection): unknown => {
    if (!session) return null;
    const status = session.sectionStatuses.find(s => s.section === section);
    return status || null;
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