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


def test_free_plan_always_usable():
    access = evaluate_tenant_access(_tenant(plan='free'))
    assert access['can_use_system'] is True
    assert access['is_expired'] is False


def test_paid_plan_expired_by_period_end():
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    tenant = _tenant(
        plan='starter',
        subscription_status='active',
        settings={'plan_period_end': past},
    )
    access = evaluate_tenant_access(tenant)
    assert access['can_use_system'] is False
    assert access['is_expired'] is True


def test_paid_plan_active_with_future_period():
    future = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
    tenant = _tenant(
        plan='professional',
        subscription_status='active',
        settings={'plan_period_end': future},
    )
    access = evaluate_tenant_access(tenant)
    assert access['can_use_system'] is True


def test_canceled_status_blocks_usage():
    access = evaluate_tenant_access(
        _tenant(plan='starter', subscription_status='canceled')
    )
    assert access['can_use_system'] is False


def test_apply_plan_period_sets_settings():
    tenant = _tenant(plan='starter', settings={})
    start, end = apply_plan_period(tenant, billing_cycle='monthly')
    assert end > start
    assert tenant.settings['plan_period_end']


def test_yearly_period_longer_than_monthly():
    monthly = compute_period_end(billing_cycle='monthly')
    yearly = compute_period_end(billing_cycle='yearly')
    assert yearly > monthly
