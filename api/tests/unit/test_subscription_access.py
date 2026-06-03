"""Plan subscription access rules."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from src.core.billing.subscription_access import (
    apply_plan_period,
    compute_period_end,
    evaluate_tenant_access,
)
from src.core.models import Tenant


def _tenant(**kwargs) -> Tenant:
    t = Tenant(
        id=uuid4(),
        name='Test',
        slug='test',
        plan=kwargs.get('plan', 'free'),
        subscription_status=kwargs.get('subscription_status', 'active'),
        settings=kwargs.get('settings', {}),
    )
    return t


def test_free_plan_allows_limited_usage():
    access = evaluate_tenant_access(_tenant(plan='free'))
    assert access['can_use_system'] is True
    assert access['upgrade_required'] is False


def test_paid_plan_expired_grace_period(monkeypatch):
    monkeypatch.setattr(
        'src.core.billing.subscription_access.subscription_expiry_enforced',
        lambda: True,
    )
    past_1d = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    tenant = _tenant(
        plan='starter',
        subscription_status='active',
        settings={'plan_period_end': past_1d},
    )
    access = evaluate_tenant_access(tenant)
    assert access['can_use_system'] is True
    assert access['is_expired'] is False
    assert access['status'] == 'grace_period'


def test_paid_plan_expired_beyond_grace_period(monkeypatch):
    monkeypatch.setattr(
        'src.core.billing.subscription_access.subscription_expiry_enforced',
        lambda: True,
    )
    past_5d = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
    tenant = _tenant(
        plan='starter',
        subscription_status='active',
        settings={'plan_period_end': past_5d},
    )
    access = evaluate_tenant_access(tenant)
    assert access['can_use_system'] is False
    assert access['is_expired'] is True


def test_dev_mode_skips_expiry_block(monkeypatch):
    monkeypatch.setattr(
        'src.core.billing.subscription_access.subscription_expiry_enforced',
        lambda: False,
    )
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    tenant = _tenant(
        plan='starter',
        subscription_status='expired',
        settings={'plan_period_end': past},
    )
    access = evaluate_tenant_access(tenant)
    assert access['can_use_system'] is True
    assert access['enforcement'] == 'quotas_only'


def test_paid_plan_active_with_future_period():
    future = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
    tenant = _tenant(
        plan='professional',
        subscription_status='active',
        settings={'plan_period_end': future},
    )
    access = evaluate_tenant_access(tenant)
    assert access['can_use_system'] is True


def test_canceled_status_blocks_usage(monkeypatch):
    monkeypatch.setattr(
        'src.core.billing.subscription_access.subscription_expiry_enforced',
        lambda: True,
    )
    access = evaluate_tenant_access(
        _tenant(plan='starter', subscription_status='canceled')
    )
    assert access['can_use_system'] is False


def test_apply_plan_period_sets_settings():
    tenant = _tenant(plan='starter', settings={})
    start, end = apply_plan_period(tenant, billing_cycle='monthly', period_days=30)
    assert end > start
    assert tenant.settings['plan_period_end']


def test_compute_period_end_default():
    end = compute_period_end()
    now = datetime.now(timezone.utc)
    assert end > now
    assert end < now + timedelta(days=31)

def test_compute_period_end_custom_days():
    end = compute_period_end(period_days=60)
    now = datetime.now(timezone.utc)
    assert end > now + timedelta(days=59)
    assert end < now + timedelta(days=61)
