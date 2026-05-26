"""Platform-wide settings (pricing, AI defaults, landing CMS) — TenderIQ Lite."""

from __future__ import annotations

import copy
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import PlatformSetting

SETTING_KEYS = ('pricing', 'ai_defaults', 'landing', 'demo_limits')

DEFAULT_PRICING: dict[str, Any] = {
    'currency': 'INR',
    'plans': [
        {
            'id': 'starter',
            'name': 'Starter',
            'description': 'Perfect for small teams getting started',
            'monthly_inr': 999,
            'yearly_inr': 9990,
            'popular': False,
            'features': [
                '100 Documents/month',
                '50 AI analyses/month',
                'Email support',
            ],
        },
        {
            'id': 'professional',
            'name': 'Professional',
            'description': 'For growing teams with advanced needs',
            'monthly_inr': 2999,
            'yearly_inr': 29990,
            'popular': True,
            'features': [
                '500 Documents/month',
                '200 AI analyses/month',
                'Proposal generator',
                'Priority support',
            ],
        },
        {
            'id': 'enterprise',
            'name': 'Enterprise',
            'description': 'Custom limits and dedicated support',
            'monthly_inr': None,
            'yearly_inr': None,
            'popular': False,
            'contact_sales': True,
            'features': ['Unlimited usage', 'SSO', 'Dedicated support'],
        },
    ],
}

DEFAULT_AI_DEFAULTS: dict[str, Any] = {
    'default_provider': 'openai',
    'default_model': '',
    'auto_analyze_on_upload': True,
    'allowed_providers': ['openai', 'anthropic', 'gemini', 'ollama'],
}

DEFAULT_LANDING: dict[str, Any] = {
    'meta': {
        'title': 'TenderIQ — AI Tender Analysis & Proposals',
        'description': 'Upload RFPs, analyze risks with your AI key, and export proposal PDFs. Free demo plan included.',
    },
    'hero': {
        'headline': 'Win More Tenders\nWith AI Intelligence',
        'subheadline': 'Upload RFPs, extract risks and deadlines, and generate proposals in minutes.',
        'cta_primary': 'Get Started Free',
        'cta_secondary': 'See pricing',
    },
    'social_proof': {
        'tagline': 'Trusted by procurement teams',
        'logos': ['TechCorp', 'BuildRight', 'GlobalServices', 'SecureVault'],
    },
    'features': [
        {
            'title': 'AI document analysis',
            'description': 'Parse PDFs and DOCX with your OpenAI, Anthropic, Gemini, or Ollama key.',
        },
        {
            'title': 'Risk & deadlines',
            'description': 'Surface compliance risks, important clauses, and submission dates.',
        },
        {
            'title': 'Proposal generator',
            'description': 'Draft sections from analysis, then export a branded PDF.',
        },
        {
            'title': 'Demo quotas',
            'description': 'Start free with monthly limits — upgrade via Razorpay when ready.',
        },
    ],
    'testimonials': [
        {
            'quote': 'We cut tender review time in half and stopped missing key deadlines.',
            'author': 'Sarah Johnson',
            'role': 'Procurement Manager',
            'company': 'TechCorp',
        },
        {
            'quote': 'Proposal PDFs with our company header went out the same day as analysis.',
            'author': 'Michael Chen',
            'role': 'Bid Manager',
            'company': 'BuildRight',
        },
    ],
    'faq': [
        {
            'question': 'Do I need my own AI API key?',
            'answer': 'Yes. Connect OpenAI, Anthropic, Gemini, or Ollama in Settings → AI.',
        },
        {
            'question': 'Is there a free plan?',
            'answer': 'Yes — demo quotas for uploads, analysis, proposals, and PDF exports.',
        },
    ],
    'cta': {
        'headline': 'Ready to analyze your next tender?',
        'button': 'Start free',
    },
}

DEFAULT_DEMO_LIMITS: dict[str, Any] = {
    'free': {
        'documents_per_month': 10,
        'ai_analyses_per_month': 5,
        'proposals_per_month': 3,
        'exports_per_month': 10,
        'ai_tokens_per_month': 50_000,
    },
}

DEFAULTS: dict[str, dict[str, Any]] = {
    'pricing': DEFAULT_PRICING,
    'ai_defaults': DEFAULT_AI_DEFAULTS,
    'landing': DEFAULT_LANDING,
    'demo_limits': DEFAULT_DEMO_LIMITS,
}


def _deep_merge(base: dict, patch: dict) -> dict:
    out = copy.deepcopy(base)
    for key, val in patch.items():
        if isinstance(val, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], val)
        else:
            out[key] = val
    return out


async def _load_row(db: AsyncSession, key: str) -> Optional[dict]:
    try:
        row = await db.get(PlatformSetting, key)
    except (OperationalError, ProgrammingError) as exc:
        logger.warning('platform_settings table unavailable (%s), using defaults', exc)
        return None
    if row and isinstance(row.value_json, dict):
        return row.value_json
    return None


async def get_setting(db: AsyncSession, key: str) -> dict[str, Any]:
    if key not in DEFAULTS:
        raise ValueError(f'Unknown setting key: {key}')
    stored = await _load_row(db, key)
    if not stored:
        return copy.deepcopy(DEFAULTS[key])
    return _deep_merge(DEFAULTS[key], stored)


async def get_all_settings(db: AsyncSession) -> dict[str, Any]:
    return {k: await get_setting(db, k) for k in SETTING_KEYS}


async def patch_setting(db: AsyncSession, key: str, patch: dict[str, Any]) -> dict[str, Any]:
    if key not in DEFAULTS:
        raise ValueError(f'Unknown setting key: {key}')
    current = await get_setting(db, key)
    merged = _deep_merge(current, patch)
    row = await db.get(PlatformSetting, key)
    if row:
        row.value_json = merged
    else:
        db.add(PlatformSetting(key=key, value_json=merged))
    await db.commit()
    return merged


def pricing_amount_paise(plan_id: str, billing_interval: str, pricing: Optional[dict] = None) -> Optional[int]:
    """Resolve Razorpay amount from admin pricing or built-in defaults."""
    from ..billing.razorpay_lite import PLAN_AMOUNT_PAISE, normalize_plan_id

    api_plan = normalize_plan_id(plan_id)
    cycle = 'yearly' if billing_interval in ('yearly', 'annual') else 'monthly'
    if pricing and pricing.get('plans'):
        for p in pricing['plans']:
            if p.get('id') != api_plan:
                continue
            inr = p.get('yearly_inr') if cycle == 'yearly' else p.get('monthly_inr')
            if inr is None:
                return None
            return int(inr) * 100
    return PLAN_AMOUNT_PAISE.get((api_plan, cycle))


async def build_public_site(db: AsyncSession) -> dict[str, Any]:
    pricing = await get_setting(db, 'pricing')
    landing = await get_setting(db, 'landing')
    return {
        'pricing': pricing,
        'landing': landing,
        'updated_at': None,
    }
