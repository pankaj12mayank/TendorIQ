import { create } from 'zustand';
import { 
  ReviewSession,
  ReviewSection,
  EditFieldPayload,
  ApprovalAction,
  RegenerationRequest,
  ReviewComment,
  AuditEntry,
  ChangeRecord,
  SectionStatus
} from './types';


interface EditState {
  section: ReviewSection | null;
  field: string | null;
  isEditing: boolean;
  originalValue: unknown;
  currentValue: unknown;
}

interface RegenerationState {
  section: ReviewSection | null;
  isRegenerating: boolean;
  progress: number;
  status: 'idle' | 'generating' | 'completed' | 'failed';
  error?: string;
}

interface ReviewState {
  session: ReviewSession | null;
  isLoading: boolean;
  isSaving: boolean;
  editState: EditState;
  regenerationState: RegenerationState;
  selectedSection: ReviewSection;
  showAuditLog: boolean;
  showChangeHistory: boolean;

  setSession: (session: ReviewSession) => void;
  setLoading: (loading: boolean) => void;
  setSelectedSection: (section: ReviewSection) => void;
  
  startEdit: (section: ReviewSection, field: string, value: unknown) => void;
  updateEditValue: (value: unknown) => void;
  saveEdit: () => Promise<void>;
  cancelEdit: () => void;
  
  submitApproval: (action: ApprovalAction, comments?: string) => Promise<void>;
  requestChanges: (sections: string[], comments: string) => Promise<void>;
  
  regenerateSection: (request: RegenerationRequest) => Promise<void>;
  updateRegenerationProgress: (progress: number) => void;
  
  addComment: (comment: Omit<ReviewComment, 'id' | 'createdAt' | 'isResolved'>) => void;
  resolveComment: (commentId: string) => void;
  addReply: (commentId: string, reply: Omit<ReviewComment, 'id' | 'createdAt' | 'isResolved' | 'replies'>) => void;
  
  toggleAuditLog: () => void;
  toggleChangeHistory: () => void;
  
  getSectionStatus: (section: ReviewSection) => SectionStatus | undefined;
}

export const useReviewStore = create<ReviewState>((set, get) => ({
  session: null,
  isLoading: false,
  isSaving: false,
  editState: {
    section: null,
    field: null,
    isEditing: false,
    originalValue: null,
    currentValue: null,
  },
  regenerationState: {
    section: null,
    isRegenerating: false,
    progress: 0,
    status: 'idle',
  },
  selectedSection: 'summary',
  showAuditLog: false,
  showChangeHistory: false,

  setSession: (session) => set({ session }),
  setLoading: (loading) => set({ isLoading: loading }),
  setSelectedSection: (section) => set({ selectedSection: section }),

  startEdit: (section, field, value) =>
    set({
      editState: {
        section,
        field,
        isEditing: true,
        originalValue: value,
        currentValue: value,
      },
    }),

  updateEditValue: (value) =>
    set((state) => ({
      editState: { ...state.editState, currentValue: value },
    })),

  saveEdit: async () => {
    const { editState, session } = get();
    if (!editState.section || !editState.field || !session) return;

    set({ isSaving: true });

    await new Promise((resolve) => setTimeout(resolve, 500));

    const newChange: ChangeRecord = {
      id: `change-${Date.now()}`,
      section: editState.section,
      field: editState.field,
      previousValue: String(editState.originalValue),
      newValue: String(editState.currentValue),
      changedBy: 'current-user',
      changedByName: 'Current User',
      changedAt: new Date().toISOString(),
    };

    const newAuditEntry: AuditEntry = {
      id: `audit-${Date.now()}`,
      action: 'SECTION_EDITED',
      performedBy: 'current-user',
      performedByName: 'Current User',
      performedByRole: 'Reviewer',
      timestamp: new Date().toISOString(),
      details: `Edited ${editState.section}.${editState.field}`,
      previousState: { [editState.field]: editState.originalValue },
      newState: { [editState.field]: editState.currentValue },
    };

    set((state) => ({
      session: state.session
        ? {
            ...state.session,
            changes: [newChange, ...state.session.changes],
            auditLog: [newAuditEntry, ...state.session.auditLog],
            sectionStatuses: state.session.sectionStatuses.map((s) =>
              s.section === editState.section
                ? { ...s, isEdited: true, hasChanges: true, editCount: s.editCount + 1, lastEditedAt: new Date().toISOString(), lastEditedBy: 'Current User' }
                : s
            ),
          }
        : null,
      editState: { section: null, field: null, isEditing: false, originalValue: null, currentValue: null },
      isSaving: false,
    }));
  },

  cancelEdit: () =>
    set({
      editState: { section: null, field: null, isEditing: false, originalValue: null, currentValue: null },
    }),

  submitApproval: async (action, comments) => {
    const { session } = get();
    if (!session) return;

    set({ isLoading: true });
    await new Promise((resolve) => setTimeout(resolve, 1000));

    const newAuditEntry: AuditEntry = {
      id: `audit-${Date.now()}`,
      action: action === 'approve' ? 'APPROVAL_SUBMITTED' : 'REQUEST_CHANGES',
      performedBy: 'current-user',
      performedByName: 'Current User',
      performedByRole: 'Reviewer',
      timestamp: new Date().toISOString(),
      details: comments || `Action: ${action}`,
    };

    set((state) => ({
      session: state.session
        ? {
            ...state.session,
            workflow: {
              ...state.session.workflow,
              status: action === 'approve' ? 'approved' : 'changes_requested',
            },
            auditLog: [newAuditEntry, ...state.session.auditLog],
          }
        : null,
      isLoading: false,
    }));
  },

  requestChanges: async (sections, comments) => {
    const { session } = get();
    if (!session) return;

    set({ isLoading: true });
    await new Promise((resolve) => setTimeout(resolve, 1000));

    const newAuditEntry: AuditEntry = {
      id: `audit-${Date.now()}`,
      action: 'REQUEST_CHANGES',
      performedBy: 'current-user',
      performedByName: 'Current User',
      performedByRole: 'Reviewer',
      timestamp: new Date().toISOString(),
      details: `Changes requested for sections: ${sections.join(', ')}. ${comments}`,
    };

    set((state) => ({
      session: state.session
        ? {
            ...state.session,
            workflow: { ...state.session.workflow, status: 'changes_requested' },
            auditLog: [newAuditEntry, ...state.session.auditLog],
          }
        : null,
      isLoading: false,
    }));
  },

  regenerateSection: async (request) => {
    set({
      regenerationState: {
        section: request.section,
        isRegenerating: true,
        progress: 0,
        status: 'generating',
      },
    });

    for (let i = 0; i <= 100; i += 20) {
      await new Promise((resolve) => setTimeout(resolve, 300));
      get().updateRegenerationProgress(i);
    }

    set((state) => ({
      regenerationState: { ...state.regenerationState, isRegenerating: false, status: 'completed', progress: 100 },
    }));

    await new Promise((resolve) => setTimeout(resolve, 500));
    set((state) => ({
      regenerationState: { section: null, isRegenerating: false, progress: 0, status: 'idle' },
    }));
  },

  updateRegenerationProgress: (progress) =>
    set((state) => ({
      regenerationState: { ...state.regenerationState, progress },
    })),

  addComment: (comment) => {
    const { session } = get();
    if (!session) return;

    const newComment: ReviewComment = {
      ...comment,
      id: `comment-${Date.now()}`,
      createdAt: new Date().toISOString(),
      isResolved: false,
    };

    const newAuditEntry: AuditEntry = {
      id: `audit-${Date.now()}`,
      action: 'COMMENT_ADDED',
      performedBy: comment.reviewerId,
      performedByName: comment.reviewerName,
      performedByRole: comment.reviewerRole,
      timestamp: new Date().toISOString(),
      details: `Comment added on ${comment.section || 'general'} section`,
    };

    set((state) => ({
      session: state.session
        ? {
            ...state.session,
            comments: [newComment, ...state.session.comments],
            auditLog: [newAuditEntry, ...state.session.auditLog],
          }
        : null,
    }));
  },

  resolveComment: (commentId) =>
    set((state) => ({
      session: state.session
        ? {
            ...state.session,
            comments: state.session.comments.map((c) =>
              c.id === commentId ? { ...c, isResolved: true } : c
            ),
          }
        : null,
    })),

  addReply: (commentId, reply) => {
    const { session } = get();
    if (!session) return;

    const newReply: ReviewComment = {
      ...reply,
      id: `reply-${Date.now()}`,
      createdAt: new Date().toISOString(),
      isResolved: false,
    };

    set((state) => ({
      session: state.session
        ? {
            ...state.session,
            comments: state.session.comments.map((c) =>
              c.id === commentId
                ? { ...c, replies: [...(c.replies || []), newReply] }
                : c
            ),
          }
        : null,
    }));
  },

  toggleAuditLog: () => set((state) => ({ showAuditLog: !state.showAuditLog })),
  toggleChangeHistory: () => set((state) => ({ showChangeHistory: !state.showChangeHistory })),

  getSectionStatus: (section) => {
    const { session } = get();
    return session?.sectionStatuses.find((s) => s.section === section);
  },
}));