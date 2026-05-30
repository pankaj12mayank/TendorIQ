"""Phase 7 — demo quotas and billing helpers."""

import pytest

from src.core.billing.lite_usage import get_plan_limits, LITE_DEMO_LIMITS
from src.core.billing.razorpay_lite import plan_amount_paise


def test_demo_limits_exist():
    assert LITE_DEMO_LIMITS['free']['documents_per_month'] == 10


def test_get_plan_limits_defaults_free():
    assert get_plan_limits('unknown')['ai_analyses_per_month'] == 5


def test_plan_amount_paise_starter():
    assert plan_amount_paise('plan_pro', 'monthly') == 9900


def test_plan_amount_free_raises():
    with pytest.raises(ValueError):
        plan_amount_paise('free', 'monthly')
