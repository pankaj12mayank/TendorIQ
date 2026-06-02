"""Layer 11 — analysis dashboard mapping and route ordering."""

from pathlib import Path

from src.core.analysis_mapper import (
    analysis_row_to_dashboard,
    empty_dashboard_analysis,
)


def test_empty_dashboard_analysis_shape():
    out = empty_dashboard_analysis('550e8400-e29b-41d4-a716-446655440000')
    assert out['tenderId'] == '550e8400-e29b-41d4-a716-446655440000'
    assert out['summary']['overallAssessment']
    assert 'eligibility' in out


def test_analysis_row_uses_stored_dashboard_payload():
    class Row:
        result = {
            'tenderId': 't1',
            'status': 'completed',
            'summary': {
                'confidence': {'value': 0.9, 'label': 'High'},
                'keyFindings': ['ok'],
                'overallAssessment': 'Ready',
            },
            'eligibility': {'overallScore': 80, 'criteria': []},
            'technical': {'complianceRate': 70, 'requirements': []},
            'financial': {'totalValue': 1, 'currency': 'USD', 'items': []},
            'risks': {'overallRiskScore': 10, 'risks': []},
            'deadlines': {'deadlines': []},
            'mandatoryDocs': {'overallCompletion': 50, 'documents': []},
        }
        summary = None
        score = None
        confidence = None
        created_at = None

    out = analysis_row_to_dashboard('t1', Row())
    assert out['summary']['overallAssessment'] == 'Ready'


def test_analysis_routes_register_tender_before_id_param():
    path = Path(__file__).resolve().parents[2] / 'src' / 'api' / 'router' / 'analysis.py'
    text = path.read_text(encoding='utf-8')
    tender_idx = text.find("@router.get('/tender/{tender_id}')")
    id_idx = text.find("@router.get('/{analysis_id}')")
    assert tender_idx != -1 and id_idx != -1
    assert tender_idx < id_idx
