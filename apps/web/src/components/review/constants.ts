import { 
  ReviewSession, 
  ReviewWorkflow, 
  Reviewer,
  ReviewComment,
  ChangeRecord,
  AuditEntry,
  SectionStatus,
  ApprovalWorkflowStep
} from './types';

export const MOCK_REVIEWERS: Reviewer[] = [
  { id: '1', name: 'Sarah Johnson', email: 'sarah.johnson@company.com', role: 'analyst', avatar: undefined },
  { id: '2', name: 'Mike Chen', email: 'mike.chen@company.com', role: 'manager', avatar: undefined },
  { id: '3', name: 'Emily Davis', email: 'emily.davis@company.com', role: 'director', avatar: undefined },
];

export const MOCK_WORKFLOW: ReviewWorkflow = {
  id: 'WF-2026-001',
  tenderId: 'IIT-2026-001',
  status: 'in_review',
  currentStep: 1,
  priority: 'high',
  createdAt: '2026-05-18T08:00:00Z',
  updatedAt: '2026-05-18T14:30:00Z',
  deadline: '2026-05-25T17:00:00Z',
  steps: [
    { id: 'step-1', name: 'Initial Review', role: 'analyst', status: 'completed', approver: MOCK_REVIEWERS[0], completedAt: '2026-05-18T10:00:00Z' },
    { id: 'step-2', name: 'Manager Approval', role: 'manager', status: 'in_progress', approver: MOCK_REVIEWERS[1] },
    { id: 'step-3', name: 'Director Sign-off', role: 'director', status: 'pending' },
  ],
};

export const MOCK_COMMENTS: ReviewComment[] = [
  {
    id: 'comment-1',
    reviewerId: '1',
    reviewerName: 'Sarah Johnson',
    reviewerRole: 'Analyst',
    section: 'financial',
    content: 'The contingency amount seems low for this type of project. Consider increasing to 10%.',
    createdAt: '2026-05-18T09:30:00Z',
    isResolved: false,
    replies: [
      {
        id: 'reply-1',
        reviewerId: '2',
        reviewerName: 'Mike Chen',
        reviewerRole: 'Manager',
        content: 'Good point. Let\'s review the risk assessment for this.',
        createdAt: '2026-05-18T10:15:00Z',
        isResolved: false,
      }
    ]
  },
  {
    id: 'comment-2',
    reviewerId: '1',
    reviewerName: 'Sarah Johnson',
    reviewerRole: 'Analyst',
    section: 'technical',
    content: 'Cloud migration capability needs demonstration. Marking for review.',
    createdAt: '2026-05-18T11:00:00Z',
    isResolved: false,
  },
  {
    id: 'comment-3',
    reviewerId: '3',
    reviewerName: 'Emily Davis',
    reviewerRole: 'Director',
    section: 'summary',
    content: 'Overall summary looks comprehensive. No major concerns from my end.',
    createdAt: '2026-05-18T13:00:00Z',
    isResolved: true,
  },
];

export const MOCK_CHANGES: ChangeRecord[] = [
  {
    id: 'change-1',
    section: 'financial',
    field: 'totalValue',
    previousValue: '$2,400,000',
    newValue: '$2,500,000',
    changedBy: '1',
    changedByName: 'Sarah Johnson',
    changedAt: '2026-05-18T09:15:00Z',
    reason: 'Updated based on revised cost estimates',
  },
  {
    id: 'change-2',
    section: 'risks',
    field: 'mitigation',
    previousValue: 'Standard security protocols',
    newValue: 'End-to-end encryption; SOC 2 compliance; regular security audits',
    changedBy: '1',
    changedByName: 'Sarah Johnson',
    changedAt: '2026-05-18T10:30:00Z',
    reason: 'Enhanced security measures based on director feedback',
  },
  {
    id: 'change-3',
    section: 'eligibility',
    field: 'criteria[3].isMet',
    previousValue: 'false',
    newValue: 'true',
    changedBy: '2',
    changedByName: 'Mike Chen',
    changedAt: '2026-05-18T11:45:00Z',
    reason: 'Verified local office presence in target region',
  },
];

export const MOCK_AUDIT_LOG: AuditEntry[] = [
  {
    id: 'audit-1',
    action: 'REVIEW_STARTED',
    performedBy: '1',
    performedByName: 'Sarah Johnson',
    performedByRole: 'Analyst',
    timestamp: '2026-05-18T08:00:00Z',
    details: 'Human review workflow initiated for tender IIT-2026-001',
  },
  {
    id: 'audit-2',
    action: 'SECTION_EDITED',
    performedBy: '1',
    performedByName: 'Sarah Johnson',
    performedByRole: 'Analyst',
    timestamp: '2026-05-18T09:15:00Z',
    details: 'Modified financial.totalValue from $2,400,000 to $2,500,000',
    previousState: { totalValue: '$2,400,000' },
    newState: { totalValue: '$2,500,000' },
  },
  {
    id: 'audit-3',
    action: 'COMMENT_ADDED',
    performedBy: '1',
    performedByName: 'Sarah Johnson',
    performedByRole: 'Analyst',
    timestamp: '2026-05-18T09:30:00Z',
    details: 'Added comment on financial section',
  },
  {
    id: 'audit-4',
    action: 'WORKFLOW_ADVANCED',
    performedBy: '1',
    performedByName: 'Sarah Johnson',
    performedByRole: 'Analyst',
    timestamp: '2026-05-18T10:00:00Z',
    details: 'Initial review completed. Workflow moved to Manager Approval.',
  },
  {
    id: 'audit-5',
    action: 'SECTION_REGENERATED',
    performedBy: '2',
    performedByName: 'Mike Chen',
    performedByRole: 'Manager',
    timestamp: '2026-05-18T12:00:00Z',
    details: 'Regenerated technical section with updated compliance data',
  },
  {
    id: 'audit-6',
    action: 'APPROVAL_SUBMITTED',
    performedBy: '2',
    performedByName: 'Mike Chen',
    performedByRole: 'Manager',
    timestamp: '2026-05-18T14:30:00Z',
    details: 'Manager approval submitted with comments',
  },
];

export const MOCK_SECTION_STATUSES: SectionStatus[] = [
  { section: 'summary', isEdited: false, hasChanges: false, editCount: 0, approvalStatus: 'approved' },
  { section: 'eligibility', isEdited: true, hasChanges: true, editCount: 2, lastEditedAt: '2026-05-18T11:45:00Z', lastEditedBy: 'Mike Chen', approvalStatus: 'approved' },
  { section: 'technical', isEdited: true, hasChanges: true, editCount: 1, lastEditedAt: '2026-05-18T12:00:00Z', lastEditedBy: 'Mike Chen', approvalStatus: 'needs_revision' },
  { section: 'financial', isEdited: true, hasChanges: true, editCount: 1, lastEditedAt: '2026-05-18T09:15:00Z', lastEditedBy: 'Sarah Johnson', approvalStatus: 'pending' },
  { section: 'risks', isEdited: true, hasChanges: true, editCount: 1, lastEditedAt: '2026-05-18T10:30:00Z', lastEditedBy: 'Sarah Johnson', approvalStatus: 'pending' },
  { section: 'deadlines', isEdited: false, hasChanges: false, editCount: 0, approvalStatus: 'approved' },
  { section: 'mandatory_docs', isEdited: false, hasChanges: false, editCount: 0, approvalStatus: 'approved' },
];

export const MOCK_REVIEW_SESSION: ReviewSession = {
  id: 'RS-2026-001',
  tenderId: 'IIT-2026-001',
  workflow: MOCK_WORKFLOW,
  reviewers: MOCK_REVIEWERS,
  comments: MOCK_COMMENTS,
  changes: MOCK_CHANGES,
  auditLog: MOCK_AUDIT_LOG,
  sectionStatuses: MOCK_SECTION_STATUSES,
  createdAt: '2026-05-18T08:00:00Z',
  updatedAt: '2026-05-18T14:30:00Z',
};

export const REVIEW_SECTIONS = [
  { id: 'summary', label: 'Summary', icon: 'file-text' },
  { id: 'eligibility', label: 'Eligibility', icon: 'check-circle' },
  { id: 'technical', label: 'Technical', icon: 'cpu' },
  { id: 'financial', label: 'Financial', icon: 'dollar-sign' },
  { id: 'risks', label: 'Risks', icon: 'alert-triangle' },
  { id: 'deadlines', label: 'Deadlines', icon: 'clock' },
  { id: 'mandatory_docs', label: 'Documents', icon: 'folder' },
] as const;

export const AUDIT_ACTIONS = {
  REVIEW_STARTED: 'Review Started',
  SECTION_EDITED: 'Section Edited',
  SECTION_REGENERATED: 'Section Regenerated',
  COMMENT_ADDED: 'Comment Added',
  COMMENT_RESOLVED: 'Comment Resolved',
  WORKFLOW_ADVANCED: 'Workflow Advanced',
  APPROVAL_SUBMITTED: 'Approval Submitted',
  APPROVAL_REJECTED: 'Approval Rejected',
  REQUEST_CHANGES: 'Changes Requested',
};

export const STATUS_COLORS = {
  pending: 'bg-gray-100 text-gray-800',
  in_review: 'bg-blue-100 text-blue-800',
  changes_requested: 'bg-yellow-100 text-yellow-800',
  approved: 'bg-green-100 text-green-800',
  rejected: 'bg-red-100 text-red-800',
};

export const PRIORITY_COLORS = {
  low: 'bg-gray-100 text-gray-800',
  medium: 'bg-blue-100 text-blue-800',
  high: 'bg-orange-100 text-orange-800',
  urgent: 'bg-red-100 text-red-800',
};