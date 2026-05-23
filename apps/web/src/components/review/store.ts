import { create } from 'zustand';
import {
  ReviewSession,
  ReviewSection,
  ReviewComment,
  AuditEntry,
  SectionStatus,
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
  activeTenderId: string | null;
  isLoading: boolean;
  isSaving: boolean;
  editState: EditState;
  regenerationState: RegenerationState;
  selectedSection: ReviewSection;
  showAuditLog: boolean;
  showChangeHistory: boolean;

  setActiveTenderId: (tenderId: string | null) => void;
  setSession: (session: ReviewSession | null) => void;
  setLoading: (loading: boolean) => void;
  setSaving: (saving: boolean) => void;
  setSelectedSection: (section: ReviewSection) => void;

  startEdit: (section: ReviewSection, field: string, value: unknown) => void;
  updateEditValue: (value: unknown) => void;
  cancelEdit: () => void;

  setRegenerationProgress: (
    section: ReviewSection | null,
    progress: number,
    status: RegenerationState['status']
  ) => void;
  clearRegeneration: () => void;

  addCommentLocal: (comment: ReviewComment) => void;
  resolveComment: (commentId: string) => void;
  addReply: (
    commentId: string,
    reply: Omit<ReviewComment, 'id' | 'createdAt' | 'isResolved' | 'replies'>
  ) => void;

  toggleAuditLog: () => void;
  toggleChangeHistory: () => void;

  getSectionStatus: (section: ReviewSection) => SectionStatus | undefined;
}

export const useReviewStore = create<ReviewState>((set, get) => ({
  session: null,
  activeTenderId: null,
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

  setActiveTenderId: (tenderId) => set({ activeTenderId: tenderId }),
  setSession: (session) => set({ session }),
  setLoading: (loading) => set({ isLoading: loading }),
  setSaving: (saving) => set({ isSaving: saving }),
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

  cancelEdit: () =>
    set({
      editState: {
        section: null,
        field: null,
        isEditing: false,
        originalValue: null,
        currentValue: null,
      },
    }),

  setRegenerationProgress: (section, progress, status) =>
    set({
      regenerationState: {
        section,
        isRegenerating: status === 'generating',
        progress,
        status,
      },
    }),

  clearRegeneration: () =>
    set({
      regenerationState: {
        section: null,
        isRegenerating: false,
        progress: 0,
        status: 'idle',
      },
    }),

  addCommentLocal: (comment) => {
    const { session } = get();
    if (!session) return;
    set({
      session: {
        ...session,
        comments: [comment, ...session.comments],
      },
    });
  },

  resolveComment: (commentId) => {
    set((state) => ({
      session: state.session
        ? {
            ...state.session,
            comments: state.session.comments.map((c) =>
              c.id === commentId ? { ...c, isResolved: true } : c
            ),
          }
        : null,
    }));
  },

  addReply: (commentId, reply) => {
    const { session } = get();
    if (!session) return;

    const newReply: ReviewComment = {
      ...reply,
      id: `reply-${Date.now()}`,
      createdAt: new Date().toISOString(),
      isResolved: false,
    };

    set({
      session: {
        ...session,
        comments: session.comments.map((c) =>
          c.id === commentId ? { ...c, replies: [...(c.replies || []), newReply] } : c
        ),
      },
    });
  },

  toggleAuditLog: () => set((state) => ({ showAuditLog: !state.showAuditLog })),
  toggleChangeHistory: () => set((state) => ({ showChangeHistory: !state.showChangeHistory })),

  getSectionStatus: (section) => {
    const { session } = get();
    return session?.sectionStatuses.find((s) => s.section === section);
  },
}));
