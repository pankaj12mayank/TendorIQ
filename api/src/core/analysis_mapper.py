"""Map AnalysisResult rows to dashboard-shaped JSON for the web UI."""

from __future__ import annotations

from typing import Any, Optional


def empty_dashboard_analysis(tender_id: str) -> dict[str, Any]:
    return {
        'tenderId': tender_id,
        'status': 'pending',
        'summary': {
            'confidence': {'value': 0.0, 'label': 'Unknown'},
            'keyFindings': [],
            'overallAssessment': 'No analysis yet',
        },
        'eligibility': {'overallScore': 0, 'criteria': []},
        'technical': {'complianceRate': 0, 'requirements': []},
        'financial': {'totalValue': 0, 'currency': 'USD', 'items': []},
        'risks': {'overallRiskScore': 0, 'risks': []},
        'deadlines': {'deadlines': []},
        'mandatoryDocs': {'overallCompletion': 0, 'documents': []},
        'importantClauses': {'clauses': []},
    }


def analysis_row_to_dashboard(tender_id: str, row: Any | None) -> dict[str, Any]:
    if row is None:
        return empty_dashboard_analysis(tender_id)

    stored = getattr(row, 'result', None) or {}
    if isinstance(stored, dict) and stored.get('tenderId'):
        return stored

    base = empty_dashboard_analysis(tender_id)
    if row.summary:
        base['summary']['overallAssessment'] = row.summary
    if row.confidence is not None:
        base['summary']['confidence'] = {
            'value': float(row.confidence),
            'label': 'High' if (row.confidence or 0) >= 0.8 else 'Medium',
        }
    if row.score is not None:
        base['eligibility']['overallScore'] = int(row.score)
    base['status'] = 'completed'
    return base
