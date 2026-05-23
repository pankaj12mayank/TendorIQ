import { useCallback, useEffect, useState } from 'react';
import { api } from '@/lib/api-client';
import { loadReviewSession } from '@/lib/review-api';
import { useReviewStore } from '@/components/review/store';
import {
  ReviewSession,
  ReviewSection,
  ApprovalAction,
  ReviewComment,
  AuditEntry,
  ChangeRecord,
  SectionStatus,
} from '@/components/review/types';

interface UseReviewApiReturn {
  session: ReviewSession | null;
  isLoading: boolean;
  isError: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  submitApproval: (action: ApprovalAction, comments?: string) => Promise<void>;
  requestChanges: (sections: string[], comments: string) => Promise<void>;
  addComment: (content: string, section?: string) => Promise<void>;
  regenerateSection: (section: ReviewSection, reason: string) => Promise<void>;
  saveFieldEdit: (section: ReviewSection, field: string, newValue: string, reason?: string) => Promise<void>;
  getSectionData: (section: ReviewSection) => unknown;
  getSectionStatus: (section: ReviewSection) => SectionStatus | undefined;
  getComments: (section?: ReviewSection) => ReviewComment[];
  getAuditLog: () => AuditEntry[];
  getChanges: () => ChangeRecord[];
}

export function useReviewApi(tenderId?: string): UseReviewApiReturn {
  const { session, setSession, setLoading: setStoreLoading } = useReviewStore();
  const [isLoading, setIsLoading] = useState(false);
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
    setIsLoading(true);
    setStoreLoading(true);

    try {
      const loaded = await loadReviewSession(tenderId);
      setSession(loaded);
    } catch {
      setIsError(true);
      setError('Failed to fetch review session');
      setSession(null);
    } finally {
      setIsLoading(false);
      setStoreLoading(false);
    }
  }, [setSession, setStoreLoading, tenderId]);

  useEffect(() => {
    if (tenderId) {
      void refetch();
    }
  }, [tenderId, refetch]);

  const submitApproval = useCallback(
    async (action: ApprovalAction, comments?: string) => {
      if (!tenderId) return;
      setIsError(false);
      setError(null);
      try {
        const apiAction =
          action === 'request_changes' ? 'request_changes' : action === 'reject' ? 'reject' : 'approve';
        await api.post(`/api/v1/review/session/${tenderId}/approval`, {
          action: apiAction,
          comments,
        });
        await refetch();
      } catch {
        setIsError(true);
        setError('Failed to submit approval');
      }
    },
    [refetch, tenderId]
  );

  const requestChanges = useCallback(
    async (sections: string[], comments: string) => {
      if (!tenderId) return;
      setIsError(false);
      setError(null);
      try {
        await api.post(`/api/v1/review/session/${tenderId}/approval`, {
          action: 'request_changes',
          sections,
          comments,
        });
        await refetch();
      } catch {
        setIsError(true);
        setError('Failed to request changes');
      }
    },
    [refetch, tenderId]
  );

  const addComment = useCallback(
    async (content: string, section?: string) => {
      if (!tenderId) return;
      try {
        await api.post(`/api/v1/review/session/${tenderId}/comments`, {
          content,
          section,
        });
        await refetch();
      } catch {
        setIsError(true);
        setError('Failed to add comment');
      }
    },
    [refetch, tenderId]
  );

  const regenerateSection = useCallback(
    async (section: ReviewSection, reason: string) => {
      if (!tenderId) return;
      const store = useReviewStore.getState();
      store.setRegenerationProgress(section, 0, 'generating');
      try {
        await api.post(`/api/v1/review/session/${tenderId}/regenerate`, {
          section,
          reason,
          include_changes: true,
          priority: 'normal',
        });
        store.setRegenerationProgress(section, 100, 'completed');
        await refetch();
      } catch {
        setIsError(true);
        setError('Failed to regenerate section');
        store.setRegenerationProgress(null, 0, 'failed');
      } finally {
        setTimeout(() => {
          useReviewStore.getState().clearRegeneration();
        }, 400);
      }
    },
    [refetch, tenderId]
  );

  const saveFieldEdit = useCallback(
    async (section: ReviewSection, field: string, newValue: string, reason?: string) => {
      if (!tenderId) return;
      try {
        await api.post(`/api/v1/review/session/${tenderId}/edit`, {
          section,
          field,
          new_value: newValue,
          reason,
        });
        await refetch();
      } catch {
        setIsError(true);
        setError('Failed to save edit');
      }
    },
    [refetch, tenderId]
  );

  const getSectionData = useCallback(
    (section: ReviewSection): unknown => {
      if (!session) return null;
      return session.sectionStatuses.find((s) => s.section === section) ?? null;
    },
    [session]
  );

  const getSectionStatus = useCallback(
    (section: ReviewSection): SectionStatus | undefined => {
      return session?.sectionStatuses.find((s) => s.section === section);
    },
    [session]
  );

  const getComments = useCallback(
    (section?: ReviewSection): ReviewComment[] => {
      if (!session) return [];
      if (!section) return session.comments;
      return session.comments.filter((c) => c.section === section);
    },
    [session]
  );

  const getAuditLog = useCallback((): AuditEntry[] => session?.auditLog || [], [session]);
  const getChanges = useCallback((): ChangeRecord[] => session?.changes || [], [session]);

  return {
    session,
    isLoading,
    isError,
    error,
    refetch,
    submitApproval,
    requestChanges,
    addComment,
    regenerateSection,
    saveFieldEdit,
    getSectionData,
    getSectionStatus,
    getComments,
    getAuditLog,
    getChanges,
  };
}

export function useReviewSections() {
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
    return session?.sectionStatuses.find((s) => s.section === section);
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

export function useEditWorkflow(tenderId?: string) {
  const id = tenderId ?? useReviewStore((s) => s.activeTenderId) ?? undefined;
  const { editState, startEdit, updateEditValue, cancelEdit, isSaving, setSaving, setSession } =
    useReviewStore();

  const saveEdit = useCallback(async () => {
    if (!id || !editState.section || !editState.field) return;
    setSaving(true);
    try {
      await api.post(`/api/v1/review/session/${id}/edit`, {
        section: editState.section,
        field: editState.field,
        new_value: String(editState.currentValue ?? ''),
      });
      const loaded = await loadReviewSession(id);
      setSession(loaded);
      cancelEdit();
    } finally {
      setSaving(false);
    }
  }, [cancelEdit, editState, id, setSaving, setSession]);

  return {
    editState,
    startEdit,
    updateEditValue,
    saveEdit,
    cancelEdit,
    isSaving,
  };
}

export function useApprovalWorkflow(tenderId?: string) {
  const id = tenderId ?? useReviewStore((s) => s.activeTenderId) ?? undefined;
  const { session, isLoading, setSession } = useReviewStore();

  const submitApproval = useCallback(
    async (action: ApprovalAction, comments?: string) => {
      if (!id) return;
      const apiAction =
        action === 'request_changes' ? 'request_changes' : action === 'reject' ? 'reject' : 'approve';
      await api.post(`/api/v1/review/session/${id}/approval`, { action: apiAction, comments });
      setSession(await loadReviewSession(id));
    },
    [id, setSession]
  );

  const requestChanges = useCallback(
    async (sections: string[], comments: string) => {
      if (!id) return;
      await api.post(`/api/v1/review/session/${id}/approval`, {
        action: 'request_changes',
        sections,
        comments,
      });
      setSession(await loadReviewSession(id));
    },
    [id, setSession]
  );

  return {
    workflow: session?.workflow || null,
    isLoading,
    submitApproval,
    requestChanges,
    canApprove: true,
    currentStepName:
      session?.workflow.steps.find((s) => s.status === 'in_progress')?.name || 'Unknown',
  };
}
