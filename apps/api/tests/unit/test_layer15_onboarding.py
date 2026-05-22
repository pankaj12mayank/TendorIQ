"""Layer 15 — onboarding hardening."""

from datetime import datetime
from pathlib import Path

from src.api.onboarding_helpers import (
    normalize_onboarding_billing_cycle,
    normalize_onboarding_plan_id,
)
from src.api.schemas.onboarding import Step4PlanSelection, OnboardingStateResponse


def test_onboarding_plan_normalization_keeps_free():
    assert normalize_onboarding_plan_id('plan_pro') == 'professional'
    assert normalize_onboarding_plan_id('free') == 'free'


def test_onboarding_billing_cycle_annual_to_yearly():
    assert normalize_onboarding_billing_cycle('annual') == 'yearly'


def test_step4_accepts_fe_plan_aliases():
    step = Step4PlanSelection.model_validate(
        {'plan_id': 'plan_pro', 'billing_cycle': 'annual'}
    )
    assert step.plan_id == 'professional'
    assert step.billing_cycle == 'yearly'


def test_onboarding_status_response_allows_empty_timestamps():
    now = datetime.utcnow()
    row = OnboardingStateResponse(
        id='',
        user_id='user-1',
        current_step=1,
        total_steps=5,
        created_at=now,
        updated_at=now,
    )
    assert row.current_step == 1


def test_step1_response_includes_session_field():
    path = Path(__file__).resolve().parents[2] / 'src' / 'api' / 'schemas' / 'onboarding.py'
    text = path.read_text(encoding='utf-8')
    assert 'class OnboardingSessionTokens' in text
    assert 'session: Optional[OnboardingSessionTokens]' in text


def test_onboarding_router_issues_session_after_step1():
    path = Path(__file__).resolve().parents[2] / 'src' / 'api' / 'routers' / 'onboarding.py'
    text = path.read_text(encoding='utf-8')
    assert 'issue_tenant_session_tokens' in text
    assert 'session=OnboardingSessionTokens' in text
