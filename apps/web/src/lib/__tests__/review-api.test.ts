import { describe, expect, it } from 'vitest';

import { mapReviewSessionFromApi } from '../review-api';

describe('review-api', () => {
  it('maps enveloped API session to client ReviewSession', () => {
    const session = mapReviewSessionFromApi({
      success: true,
      data: {
        id: 's1',
        tender_id: 't1',
        workflow: {
          id: 'w1',
          tender_id: 't1',
          status: 'in_review',
          current_step: 1,
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        },
        section_statuses: [
          {
            section: 'summary',
            is_edited: false,
            has_changes: false,
            edit_count: 0,
            approval_status: 'pending',
          },
        ],
        comments: [],
        changes: [],
        audit_log: [],
        reviewers: [],
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      },
    });

    expect(session.tenderId).toBe('t1');
    expect(session.workflow.status).toBe('in_review');
    expect(session.sectionStatuses[0]?.section).toBe('summary');
  });
});
