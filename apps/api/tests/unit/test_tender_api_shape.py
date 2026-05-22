"""Layer 11 — tender API JSON uses dashboard camelCase fields."""

from types import SimpleNamespace

from src.api.services.tender_service import TenderService


def test_tender_to_dict_camel_case():
    tender = SimpleNamespace(
        id='550e8400-e29b-41d4-a716-446655440000',
        title='Test',
        description='Desc',
        status='draft',
        budget=1000.0,
        currency='USD',
        closing_date=None,
        tenant_id='660e8400-e29b-41d4-a716-446655440001',
        created_at=None,
        updated_at=None,
    )
    out = TenderService._tender_to_dict(None, tender)
    assert out['closingDate'] is None
    assert out['organizationId'] == '660e8400-e29b-41d4-a716-446655440001'
    assert 'closing_date' not in out
