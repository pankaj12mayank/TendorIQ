"""Map AnalysisResult rows to the dashboard TenderAnalysis JSON shape."""

from __future__ import annotations

from typing import Any, Optional

from ...core.models import AnalysisResult


def _confidence(value: float = 0) -> dict[str, Any]:
    label = 'High' if value >= 0.8 else 'Medium' if value >= 0.5 else 'Low'
    return {'value': value, 'label': label, 'factors': []}


def empty_dashboard_analysis(tender_id: str) -> dict[str, Any]:
    return {
        'tenderId': tender_id,
        'status': 'pending',
        'summary': {
            'confidence': _confidence(0),
            'keyFindings': [],
            'overallAssessment': 'No analysis has been run for this tender yet.',
        },
        'eligibility': {
            'overallScore': 0,
            'criteria': [],
        },
        'technical': {
            'complianceRate': 0,
            'requirements': [],
        },
        'financial': {
            'totalValue': 0,
            'currency': 'USD',
            'items': [],
        },
        'risks': {
            'overallRiskScore': 0,
            'risks': [],
        },
        'deadlines': {
            'deadlines': [],
        },
        'mandatoryDocs': {
            'overallCompletion': 0,
            'documents': [],
        },
        'createdAt': '',
        'updatedAt': '',
    }


def analysis_row_to_dashboard(tender_id: str, row: Optional[AnalysisResult]) -> dict[str, Any]:
    if not row:
        return empty_dashboard_analysis(tender_id)

    payload = row.result if isinstance(row.result, dict) else {}
    if payload.get('summary') and (payload.get('tenderId') or payload.get('tender_id')):
        out = dict(payload)
        out['tenderId'] = str(payload.get('tenderId') or payload.get('tender_id') or tender_id)
        out.setdefault('status', 'completed')
        out.setdefault('createdAt', row.created_at.isoformat() if row.created_at else None)
        out.setdefault('updatedAt', row.created_at.isoformat() if row.created_at else None)
        return out

    base = empty_dashboard_analysis(tender_id)
    conf = float(row.confidence) if row.confidence is not None else 0.0
    if row.summary:
        base['summary']['overallAssessment'] = row.summary
    base['summary']['confidence'] = _confidence(conf)
    if row.score is not None:
        base['eligibility']['overallScore'] = int(row.score)
    base['status'] = 'completed' if row.summary or payload else 'in_progress'
    base['createdAt'] = row.created_at.isoformat() if row.created_at else None
    base['updatedAt'] = row.created_at.isoformat() if row.created_at else None
    if payload:
        for key in ('eligibility', 'technical', 'financial', 'risks', 'deadlines', 'mandatoryDocs'):
            if key in payload:
                base[key] = payload[key]
    return base
