export type ReviewStatus = 'pending' | 'in_review' | 'changes_requested' | 'approved' | 'rejected';

export type ApprovalAction = 'submit' | 'approve' | 'request_changes' | 'reject' | 'regenerate';

export interface Reviewer {
  id: string;
  name: string;
  email: string;
  role: 'analyst' | 'manager' | 'director' | 'admin';
  avatar?: string;
}

export interface ReviewComment {
  id: string;
  reviewerId: string;
  reviewerName: string;
  reviewerRole: string;
  content: string;
  section?: string;
  createdAt: string;
  updatedAt?: string;
  isResolved: boolean;
  replies?: ReviewComment[];
}

export interface ChangeRecord {
  id: string;
  section: string;
  field: string;
  previousValue: string;
  newValue: string;
  changedBy: string;
  changedByName: string;
  changedAt: string;
  reason?: string;
}

export interface AuditEntry {
  id: string;
  action: string;
  performedBy: string;
  performedByName: string;
  performedByRole: string;
  timestamp: string;
  details: string;
  previousState?: Record<string, unknown>;
  newState?: Record<string, unknown>;
  ipAddress?: string;
  userAgent?: string;
}

export interface SectionStatus {
  section: string;
  isEdited: boolean;
  hasChanges: boolean;
  editCount: number;
  lastEditedAt?: string;
  lastEditedBy?: string;
  approvalStatus: 'pending' | 'approved' | 'rejected' | 'needs_revision';
}

export interface ApprovalWorkflowStep {
  id: string;
  name: string;
  role: Reviewer['role'];
  status: 'pending' | 'in_progress' | 'completed' | 'skipped';
  approver?: Reviewer;
  completedAt?: string;
  comments?: string;
  signature?: string;
}

export interface ReviewWorkflow {
  id: string;
  tenderId: string;
  status: ReviewStatus;
  currentStep: number;
  steps: ApprovalWorkflowStep[];
  createdAt: string;
  updatedAt: string;
  deadline?: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
}

export interface ReviewSession {
  id: string;
  tenderId: string;
  workflow: ReviewWorkflow;
  reviewers: Reviewer[];
  comments: ReviewComment[];
  changes: ChangeRecord[];
  auditLog: AuditEntry[];
  sectionStatuses: SectionStatus[];
  createdAt: string;
  updatedAt: string;
}

export interface RegenerationRequest {
  section: string;
  reason: string;
  includeChanges: boolean;
  priority: 'normal' | 'high';
}

export interface ApprovalRequest {
  workflowId: string;
  action: ApprovalAction;
  comments?: string;
  sections?: string[];
}

export interface EditFieldPayload {
  section: string;
  field: string;
  oldValue: unknown;
  newValue: unknown;
  reason?: string;
}

export type ReviewSection = 
  | 'summary'
  | 'eligibility'
  | 'technical'
  | 'financial'
  | 'risks'
  | 'deadlines'
  | 'mandatory_docs';

export interface EditState {
  section: ReviewSection;
  field: string;
  isEditing: boolean;
  originalValue: unknown;
  currentValue: unknown;
  isSaving: boolean;
}

export interface RegenerationState {
  section: ReviewSection;
  isRegenerating: boolean;
  progress: number;
  status: 'idle' | 'generating' | 'completed' | 'failed';
  error?: string;
}