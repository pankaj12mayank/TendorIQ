"""Phase 5 — lite proposal helpers."""

from src.core.proposal.lite_service import (
    build_proposal_pdf_data,
    company_profile_to_text,
    dashboard_to_tender_text,
)


def test_company_profile_to_text_includes_name():
    text = company_profile_to_text({'company_name': 'Acme Ltd', 'phone': '+1'})
    assert 'Acme Ltd' in text
    assert '+1' in text


def test_company_profile_empty_hint():
    assert 'Settings' in company_profile_to_text(None)


def test_build_proposal_pdf_data_organization():
    proposal = {
        'title': 'Test Proposal',
        'status': 'completed',
        'sections': [{'title': 'Summary', 'content': 'Hello', 'word_count': 1}],
    }
    company = {'company_name': 'Acme', 'address': '123 St', 'phone': '555'}
    data = build_proposal_pdf_data(proposal, company)
    assert data['title'] == 'Test Proposal'
    assert 'Acme' in data['organization']
    assert '123 St' in data['organization']


def test_dashboard_to_tender_text():
    text = dashboard_to_tender_text({
        'status': 'completed',
        'summary': {'overallAssessment': 'Good fit', 'keyFindings': ['A']},
    })
    assert 'Good fit' in text
    assert 'A' in text
