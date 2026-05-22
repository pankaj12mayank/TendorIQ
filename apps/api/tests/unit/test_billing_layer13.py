"""Layer 13 — billing API paths and FE response mappers."""

from pathlib import Path

from src.core.billing.fe_responses import (
    FE_PLAN_TO_API,
    _quota_entry,
    normalize_billing_cycle,
    normalize_plan_id,
)


def test_plan_id_normalization():
    assert normalize_plan_id('plan_pro') == 'professional'
    assert normalize_plan_id('starter') == 'starter'


def test_billing_cycle_normalization():
    assert normalize_billing_cycle('annual') == 'yearly'
    assert normalize_billing_cycle('monthly') == 'monthly'


def test_quota_entry_unlimited():
    row = _quota_entry('users', 1, -1)
    assert row['isUnlimited'] is True
    assert row['remaining'] is None


def test_billing_router_exposes_quota_and_change_paths():
    path = Path(__file__).resolve().parents[2] / 'src' / 'api' / 'router' / 'billing.py'
    text = path.read_text(encoding='utf-8')
    assert "@router.get('/quota')" in text
    assert "@router.get('/usage/summary')" in text
    assert "@router.post('/subscription/change')" in text
    assert 'require_tenant_member' in text
    assert 'parse_tenant_uuid' in text


def test_fe_plan_mapping_covers_frontend_ids():
    assert FE_PLAN_TO_API['plan_enterprise'] == 'enterprise'
