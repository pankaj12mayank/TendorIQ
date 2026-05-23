import { api } from './api-client';
import { unwrapData } from './api-envelope';
import type {
  AuditEntry,
  ChangeRecord,
  ReviewComment,
  ReviewSession,
  ReviewWorkflow,
  SectionStatus,
} from '@/components/review/types';

function mapComment(raw: Record<string, unknown>): ReviewComment {
  return {
    id: String(raw.id ?? ''),
    reviewerId: String(raw.reviewer_id ?? raw.reviewerId ?? ''),
    reviewerName: String(raw.reviewer_name ?? raw.reviewerName ?? ''),
    reviewerRole: String(raw.reviewer_role ?? raw.reviewerRole ?? 'reviewer'),
    content: String(raw.content ?? ''),
    section: raw.section != null ? String(raw.section) : undefined,
    createdAt: String(raw.created_at ?? raw.createdAt ?? new Date().toISOString()),
    isResolved: Boolean(raw.is_resolved ?? raw.isResolved ?? false),
    replies: Array.isArray(raw.replies)
      ? (raw.replies as Record<string, unknown>[]).map(mapComment)
      : [],
  };
}

function mapAudit(raw: Record<string, unknown>): AuditEntry {
  return {
    id: String(raw.id ?? ''),
    action: String(raw.action ?? ''),
    performedBy: String(raw.performed_by ?? raw.performedBy ?? ''),
    performedByName: String(raw.performed_by_name ?? raw.performedByName ?? ''),
    performedByRole: String(raw.performed_by_role ?? raw.performedByRole ?? ''),
    timestamp: String(raw.timestamp ?? raw.created_at ?? new Date().toISOString()),
    details: String(raw.details ?? raw.action ?? ''),
    previousState: (raw.previous_state ?? raw.previousState) as Record<string, unknown> | undefined,
    newState: (raw.new_state ?? raw.newState) as Record<string, unknown> | undefined,
  };
}

function mapChange(raw: Record<string, unknown>): ChangeRecord {
  return {
    id: String(raw.id ?? ''),
    section: String(raw.section ?? ''),
    field: String(raw.field ?? ''),
    previousValue: String(raw.previous_value ?? raw.previousValue ?? ''),
    newValue: String(raw.new_value ?? raw.newValue ?? ''),
    changedBy: String(raw.changed_by ?? raw.changedBy ?? ''),
    changedByName: String(raw.changed_by_name ?? raw.changedByName ?? ''),
    changedAt: String(raw.changed_at ?? raw.changedAt ?? new Date().toISOString()),
    reason: raw.reason != null ? String(raw.reason) : undefined,
  };
}

function mapSectionStatus(raw: Record<string, unknown>): SectionStatus {
  return {
    section: String(raw.section ?? ''),
    isEdited: Boolean(raw.is_edited ?? raw.isEdited ?? false),
    hasChanges: Boolean(raw.has_changes ?? raw.hasChanges ?? false),
    editCount: Number(raw.edit_count ?? raw.editCount ?? 0),
    lastEditedAt:
      raw.last_edited_at != null
        ? String(raw.last_edited_at)
        : raw.lastEditedAt != null
          ? String(raw.lastEditedAt)
          : undefined,
    lastEditedBy:
      raw.last_edited_by != null
        ? String(raw.last_edited_by)
        : raw.lastEditedBy != null
          ? String(raw.lastEditedBy)
          : undefined,
    approvalStatus: (raw.approval_status ?? raw.approvalStatus ?? 'pending') as SectionStatus['approvalStatus'],
  };
}

function mapWorkflow(raw: Record<string, unknown>, tenderId: string): ReviewWorkflow {
  return {
    id: String(raw.id ?? ''),
    tenderId: String(raw.tender_id ?? raw.tenderId ?? tenderId),
    status: (raw.status ?? 'pending') as ReviewWorkflow['status'],
    currentStep: Number(raw.current_step ?? raw.currentStep ?? 1),
    steps: Array.isArray(raw.steps)
      ? (raw.steps as Record<string, unknown>[]).map((step) => ({
          id: String(step.id ?? ''),
          name: String(step.name ?? ''),
          role: (step.role ?? 'analyst') as ReviewWorkflow['steps'][0]['role'],
          status: (step.status ?? 'pending') as ReviewWorkflow['steps'][0]['status'],
          completedAt:
            step.completed_at != null
              ? String(step.completed_at)
              : step.completedAt != null
                ? String(step.completedAt)
                : undefined,
          comments: step.comments != null ? String(step.comments) : undefined,
        }))
      : [],
    createdAt: String(raw.created_at ?? raw.createdAt ?? new Date().toISOString()),
    updatedAt: String(raw.updated_at ?? raw.updatedAt ?? new Date().toISOString()),
    deadline:
      raw.deadline != null
        ? String(raw.deadline)
        : undefined,
    priority: (raw.priority ?? 'medium') as ReviewWorkflow['priority'],
  };
}

export function mapReviewSessionFromApi(payload: unknown): ReviewSession {
  const raw = (unwrapData(payload) ?? payload) as Record<string, unknown>;
  const tenderId = String(raw.tender_id ?? raw.tenderId ?? '');
  const workflowRaw = (raw.workflow ?? {}) as Record<string, unknown>;

  return {
    id: String(raw.id ?? tenderId),
    tenderId,
    workflow: mapWorkflow(workflowRaw, tenderId),
    reviewers: Array.isArray(raw.reviewers) ? (raw.reviewers as ReviewSession['reviewers']) : [],
    comments: Array.isArray(raw.comments)
      ? (raw.comments as Record<string, unknown>[]).map(mapComment)
      : [],
    changes: Array.isArray(raw.changes)
      ? (raw.changes as Record<string, unknown>[]).map(mapChange)
      : [],
    auditLog: Array.isArray(raw.audit_log)
      ? (raw.audit_log as Record<string, unknown>[]).map(mapAudit)
      : Array.isArray(raw.auditLog)
        ? (raw.auditLog as Record<string, unknown>[]).map(mapAudit)
        : [],
    sectionStatuses: Array.isArray(raw.section_statuses)
      ? (raw.section_statuses as Record<string, unknown>[]).map(mapSectionStatus)
      : Array.isArray(raw.sectionStatuses)
        ? (raw.sectionStatuses as Record<string, unknown>[]).map(mapSectionStatus)
        : [],
    createdAt: String(raw.created_at ?? raw.createdAt ?? new Date().toISOString()),
    updatedAt: String(raw.updated_at ?? raw.updatedAt ?? new Date().toISOString()),
  };
}

export async function loadReviewSession(tenderId: string): Promise<ReviewSession> {
  const sessionRaw = await api.get<{ data?: unknown }>(`/api/v1/review/session/${tenderId}`);
  let session = mapReviewSessionFromApi(sessionRaw);

  try {
    const auditRaw = await api.get<{ data?: unknown }>(`/api/v1/review/session/${tenderId}/audit`);
    const audit = unwrapData(auditRaw);
    if (Array.isArray(audit)) {
      session = {
        ...session,
        auditLog: (audit as Record<string, unknown>[]).map(mapAudit),
      };
    }
  } catch {
    // keep session audit_log from main payload
  }

  try {
    const changesRaw = await api.get<{ data?: unknown }>(`/api/v1/review/session/${tenderId}/changes`);
    const changes = unwrapData(changesRaw);
    if (Array.isArray(changes)) {
      session = {
        ...session,
        changes: (changes as Record<string, unknown>[]).map(mapChange),
      };
    }
  } catch {
    // keep session changes from main payload
  }

  return session;
}
