"""Shared onboarding helpers (plan normalization, session tokens)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..core.billing.fe_responses import normalize_billing_cycle
from ..core.local_auth import issue_session_tokens

if TYPE_CHECKING:
    from ..dependencies.auth import AuthContext

ONBOARDING_PLAN_ALIASES = {
    'plan_free': 'free',
    'plan_starter': 'starter',
    'plan_pro': 'professional',
    'pro': 'professional',
    'plan_enterprise': 'enterprise',
}


def normalize_onboarding_plan_id(plan_id: str) -> str:
    key = (plan_id or '').strip().lower()
    return ONBOARDING_PLAN_ALIASES.get(key, key)


def normalize_onboarding_billing_cycle(cycle: str) -> str:
    return normalize_billing_cycle(cycle)


def issue_tenant_session_tokens(
    current_user: 'AuthContext',
    *,
    tenant_id: str,
    membership_role: str = 'owner',
) -> dict:
    """Re-issue JWT so subsequent onboarding steps and dashboard calls include tenant_id."""
    tokens = issue_session_tokens(
        user_id=current_user.user_id,
        email=current_user.email or '',
        role=current_user.role or 'user',
        tenant_id=tenant_id,
        membership_role=membership_role or 'owner',
    )
    return {
        'access_token': tokens['access_token'],
        'refresh_token': tokens['refresh_token'],
        'expires_in': tokens.get('expires_in', 1800),
    }
