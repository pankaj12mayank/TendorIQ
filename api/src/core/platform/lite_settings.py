"""Platform-wide settings (pricing, AI defaults, landing CMS) — TenderIQ Lite."""

from __future__ import annotations

import copy
import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import PlatformSetting

logger = logging.getLogger(__name__)

SETTING_KEYS = (
    'pricing',
    'ai_defaults',
    'landing',
    'landing_cms',
    'demo_limits',
    'smtp',
    'payment_gateways',
)

DEFAULT_PRICING: dict[str, Any] = {
    'currency': 'USD',
    'plans': [
        {
            'id': 'professional',
            'name': 'Professional',
            'description': 'Complete workflow for tender analysis and proposal generation',
            'monthly_usd': 99,
            'yearly_usd': None,
            'popular': True,
            'active': True,
            'upload_limit': 500,
            'expiry_period_days': 30,
            'features': [
                '500 documents per cycle',
                'AI analysis and risk detection',
                'Proposal generator and PDF export',
                'Priority support',
            ],
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
        'description': 'Upload RFPs, analyze risks with your AI key, and export proposal PDFs with monthly subscription plans.',
    },
    'hero': {
        'headline': 'AI Procurement Platform',
        'subheadline': 'Upload RFPs, extract risks and deadlines, and generate proposals in minutes.',
        'cta_primary': 'Start Monthly Plan',
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
            'title': 'Monthly subscription',
            'description': 'Use monthly plans with predictable limits and renewal.',
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
            'question': 'Do you offer monthly plans?',
            'answer': 'Yes. TenderIQ Lite supports monthly subscriptions.',
        },
    ],
    'cta': {
        'headline': 'Ready to analyze your next tender?',
        'button': 'Upgrade monthly',
    },
}

DEFAULT_WORKFLOW_TUTORIAL: dict[str, Any] = {
    'title': 'How TenderIQ Workflow Works',
    'subtitle': 'Follow this 5-step tutorial from upload to proposal export.',
    'steps': [
        {
            'id': 'upload',
            'title': 'Upload tender file',
            'description': 'Upload PDF/DOCX and let the pipeline register the document job.',
            'image_url': '',
        },
        {
            'id': 'extract',
            'title': 'Extract requirements',
            'description': 'System parses sections, deadlines, and qualification criteria.',
            'image_url': '',
        },
        {
            'id': 'analyze',
            'title': 'Run AI processing',
            'description': 'AI analyzes compliance, scoring, and potential risk flags.',
            'image_url': '',
        },
        {
            'id': 'review',
            'title': 'Review risk insights',
            'description': 'Validate extracted risks and mark items requiring manual review.',
            'image_url': '',
        },
        {
            'id': 'propose',
            'title': 'Generate proposal',
            'description': 'Generate proposal draft and export PDF for submission.',
            'image_url': '',
        },
    ],
}

DEFAULT_LANDING_MODULES: dict[str, Any] = {
    'meta': copy.deepcopy(DEFAULT_LANDING['meta']),
    'hero': copy.deepcopy(DEFAULT_LANDING['hero']),
    'features': copy.deepcopy(DEFAULT_LANDING['features']),
    'faq': copy.deepcopy(DEFAULT_LANDING['faq']),
    'pricing': {
        'title': 'Plans That Scale With You',
        'subtitle': 'Monthly subscriptions for procurement teams.',
        'billing_note': 'Monthly billing only.',
    },
    'trusted_by': {
        'title': 'Trusted by Procurement Teams',
        'description': 'Live platform adoption metrics',
    },
    'customer_stories': [],
    'cta': {
        'headline': 'Deploy TenderIQ in your procurement workflow',
        'button': 'Start monthly plan',
    },
    'contact': {
        'title': 'Talk to our team',
        'support_email': 'support@tendoriq.com',
    },
    'images': {
        'logo_url': '',
        'favicon_url': '',
        'hero_image_url': '',
        'auth_illustration_url': '',
        'brand_name': 'TenderIQ',
        'auth_tagline': 'Secure workspace login',
    },
    'workflow_tutorial': copy.deepcopy(DEFAULT_WORKFLOW_TUTORIAL),
}

DEFAULT_LANDING_CMS: dict[str, Any] = {
    'version': 1,
    'status': 'draft',
    'draft': copy.deepcopy(DEFAULT_LANDING_MODULES),
    'published': copy.deepcopy(DEFAULT_LANDING_MODULES),
    'history': [],
    'published_at': None,
    'updated_at': None,
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

DEFAULT_SMTP: dict[str, Any] = {
    'host': '',
    'port': 587,
    'sender_email': '',
    'sender_name': 'TenderIQ',
    'app_password': '',
}

DEFAULT_PAYMENT_GATEWAYS: dict[str, Any] = {
    'razorpay_key_id': '',
    'razorpay_key_secret': '',
    'razorpay_test_mode': True,
    'stripe_publishable_key': '',
    'stripe_secret_key': '',
    'stripe_webhook_secret': '',
    'stripe_test_mode': True,
}

DEFAULTS: dict[str, dict[str, Any]] = {
    'pricing': DEFAULT_PRICING,
    'ai_defaults': DEFAULT_AI_DEFAULTS,
    'landing': DEFAULT_LANDING,
    'landing_cms': DEFAULT_LANDING_CMS,
    'demo_limits': DEFAULT_DEMO_LIMITS,
    'smtp': DEFAULT_SMTP,
    'payment_gateways': DEFAULT_PAYMENT_GATEWAYS,
}

IMAGE_URL_RE = re.compile(r'^(https?://|/).+')
IMAGE_EXT_RE = re.compile(r'\.(png|jpe?g|webp|svg|ico)$', re.IGNORECASE)


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


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _valid_image_url(value: str) -> bool:
    if not value:
        return True
    return bool(IMAGE_URL_RE.match(value) and IMAGE_EXT_RE.search(value))


def validate_landing_cms_modules(modules: dict[str, Any]) -> None:
    if not isinstance(modules, dict):
        raise ValueError('CMS modules must be an object')
    if not isinstance(modules.get('hero', {}), dict):
        raise ValueError('hero module must be an object')
    if not isinstance(modules.get('features', []), list):
        raise ValueError('features module must be an array')
    if not isinstance(modules.get('faq', []), list):
        raise ValueError('faq module must be an array')
    if not isinstance(modules.get('cta', {}), dict):
        raise ValueError('cta module must be an object')
    if not isinstance(modules.get('images', {}), dict):
        raise ValueError('images module must be an object')
    if not isinstance(modules.get('contact', {}), dict):
        raise ValueError('contact module must be an object')
    if not isinstance(modules.get('customer_stories', []), list):
        raise ValueError('customer_stories module must be an array')
    if not isinstance(modules.get('workflow_tutorial', {}), dict):
        raise ValueError('workflow_tutorial module must be an object')
    images = modules.get('images', {})
    for key in ('logo_url', 'favicon_url', 'hero_image_url', 'auth_illustration_url'):
        raw = str(images.get(key) or '').strip()
        if not _valid_image_url(raw):
            raise ValueError(f'Invalid image URL for {key}. Use absolute URL or /path with image extension')
    support_email = str(modules.get('contact', {}).get('support_email') or '').strip()
    if support_email and ('@' not in support_email or ' ' in support_email):
        raise ValueError('Invalid support_email format')
    stories = modules.get('customer_stories', [])
    for idx, story in enumerate(stories):
        if not isinstance(story, dict):
            raise ValueError('Each customer story must be an object')
        quote = str(story.get('quote') or '').strip()
        author = str(story.get('author') or '').strip()
        if not quote or not author:
            raise ValueError(f'customer_stories[{idx}] must include quote and author')
        logo_url = str(story.get('logo_url') or '').strip()
        if logo_url and not _valid_image_url(logo_url):
            raise ValueError(f'Invalid logo_url in customer_stories[{idx}]')
    wf_steps = modules.get('workflow_tutorial', {}).get('steps', [])
    if not isinstance(wf_steps, list):
        raise ValueError('workflow_tutorial.steps must be an array')
    for idx, step in enumerate(wf_steps):
        if not isinstance(step, dict):
            raise ValueError('Each workflow step must be an object')
        if not str(step.get('title') or '').strip():
            raise ValueError(f'workflow_tutorial.steps[{idx}] title is required')
        img = str(step.get('image_url') or '').strip()
        if img and not _valid_image_url(img):
            raise ValueError(f'Invalid image_url in workflow_tutorial.steps[{idx}]')


def pricing_amount_paise(plan_id: str, billing_interval: str, pricing: Optional[dict] = None) -> Optional[int]:
    """Resolve Razorpay amount from admin pricing or built-in defaults."""
    from ..billing.razorpay_lite import PLAN_AMOUNT_PAISE, normalize_plan_id

    api_plan = normalize_plan_id(plan_id)
    cycle = 'yearly' if billing_interval in ('yearly', 'annual') else 'monthly'
    if pricing and pricing.get('plans'):
        for p in pricing['plans']:
            if p.get('id') != api_plan:
                continue
            usd = p.get('yearly_usd') if cycle == 'yearly' else p.get('monthly_usd')
            if usd is None:
                usd = p.get('yearly_inr') if cycle == 'yearly' else p.get('monthly_inr')
            if usd is None:
                return None
            return int(usd) * 100
    return PLAN_AMOUNT_PAISE.get((api_plan, cycle))


async def build_public_site(db: AsyncSession) -> dict[str, Any]:
    pricing = await get_setting(db, 'pricing')
    landing_cms = await get_setting(db, 'landing_cms')
    landing = landing_cms.get('published') or await get_setting(db, 'landing')
    validate_landing_cms_modules(landing if isinstance(landing, dict) else {})
    row = await db.get(PlatformSetting, 'landing_cms')
    return {
        'pricing': pricing,
        'landing': landing,
        'cms_state': {
            'version': int(landing_cms.get('version') or 1),
            'status': str(landing_cms.get('status') or 'draft'),
            'published_at': landing_cms.get('published_at'),
        },
        'updated_at': row.updated_at.isoformat() if row and row.updated_at else None,
    }
