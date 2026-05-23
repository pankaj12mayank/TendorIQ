import { describe, expect, it } from 'vitest';

import { parseAnalysisDashboard } from '@tendoriq/shared/analysis';
import { mapAnalysisDashboardToUi } from '../analysis-mapper';

describe('analysis dashboard mapping', () => {
  it('parses empty API payload without throwing', () => {
    const dashboard = parseAnalysisDashboard({}, 'tender-abc');
    const ui = mapAnalysisDashboardToUi(dashboard);
    expect(ui.tenderId).toBe('tender-abc');
    expect(ui.summary.keyHighlights).toEqual([]);
    expect(ui.summary.confidence.value).toBe(0);
  });

  it('maps keyFindings to keyHighlights', () => {
    const dashboard = parseAnalysisDashboard(
      {
        tenderId: 't1',
        summary: {
          keyFindings: ['Finding A'],
          overallAssessment: 'Looks good',
          confidence: { value: 0.85, label: 'High' },
        },
      },
      't1'
    );
    const ui = mapAnalysisDashboardToUi(dashboard);
    expect(ui.summary.keyHighlights).toEqual(['Finding A']);
    expect(ui.summary.confidence.value).toBe(85);
    expect(ui.summary.description).toContain('Looks good');
  });

  it('accepts mandatory_docs alias', () => {
    const dashboard = parseAnalysisDashboard(
      {
        mandatory_docs: { overallCompletion: 50, documents: [{ id: 'd1', name: 'Form', status: 'submitted' }] },
      },
      't2'
    );
    const ui = mapAnalysisDashboardToUi(dashboard);
    expect(ui.mandatoryDocs.overallCompletion).toBe(50);
    expect(ui.mandatoryDocs.documents[0]?.isSubmitted).toBe(true);
  });
});
