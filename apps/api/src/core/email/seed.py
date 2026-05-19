"""Seed default email templates and event mappings."""

import logging
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .db_models import EmailBranding, EmailEvent, EmailTemplate
from .events.registry import EVENT_REGISTRY

logger = logging.getLogger(__name__)


def _wrap(content: str) -> str:
    return f"""<div style="font-family: Inter, system-ui, sans-serif; max-width: 600px; margin: 0 auto; background: #0f172a; color: #e2e8f0; border-radius: 12px; overflow: hidden;">
  <div style="padding: 32px 24px; background: linear-gradient(135deg, #2563eb, #7c3aed);">
    <h1 style="margin:0;font-size:22px;color:#fff;">TenderIQ</h1>
  </div>
  <div style="padding:32px 24px;">{content}</div>
  <div style="padding:20px 24px;border-top:1px solid #334155;font-size:12px;color:#94a3b8;">
    © TenderIQ
  </div>
</div>"""


DEFAULT_TEMPLATES: dict[str, dict] = {
    'welcome_email': {
        'name': 'Welcome Email',
        'subject': 'Welcome to TenderIQ, {{user_name}}',
        'html': _wrap(
            '<p>Hi {{user_name}},</p><p>Your account is ready.</p>'
            '<p><a href="{{dashboard_link}}" style="background:#2563eb;color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;">Go to Dashboard</a></p>'
        ),
        'variables': ['user_name', 'dashboard_link', 'company_name'],
    },
    'reset_password': {
        'name': 'Password Reset',
        'subject': 'Reset your TenderIQ password',
        'html': _wrap(
            '<p>Hi {{user_name}},</p><p>Reset your password (expires in {{expires_in}}).</p>'
            '<p><a href="{{reset_link}}" style="background:#2563eb;color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;">Reset Password</a></p>'
        ),
        'variables': ['user_name', 'reset_link', 'expires_in'],
    },
    'verify_email': {
        'name': 'Verify Email',
        'subject': 'Verify your TenderIQ email',
        'html': _wrap('<p>Hi {{user_name}},</p><p><a href="{{verify_link}}">Verify Email</a></p>'),
        'variables': ['user_name', 'verify_link'],
    },
    'password_changed': {
        'name': 'Password Changed',
        'subject': 'Your TenderIQ password was changed',
        'html': _wrap('<p>Hi {{user_name}},</p><p>Your password was updated successfully.</p>'),
        'variables': ['user_name'],
    },
    'upload_received': {
        'name': 'Upload Received',
        'subject': 'We received {{document_name}}',
        'html': _wrap('<p>Hi {{user_name}},</p><p>Document <strong>{{document_name}}</strong> uploaded for {{tender_name}}.</p>'),
        'variables': ['user_name', 'document_name', 'tender_name'],
    },
    'processing_completed': {
        'name': 'Processing Complete',
        'subject': 'Analysis complete: {{document_name}}',
        'html': _wrap('<p>Hi {{user_name}},</p><p>Processing complete for {{document_name}}.</p>'),
        'variables': ['user_name', 'document_name', 'dashboard_link'],
    },
    'processing_failed': {
        'name': 'Processing Failed',
        'subject': 'Processing failed: {{document_name}}',
        'html': _wrap('<p>Hi {{user_name}},</p><p>Error: {{error_message}}</p>'),
        'variables': ['user_name', 'document_name', 'error_message'],
    },
    'quota_exceeded': {
        'name': 'Quota Exceeded',
        'subject': 'Usage limit: {{feature}}',
        'html': _wrap('<p>{{feature}} usage {{used}}/{{limit}} exceeded.</p>'),
        'variables': ['feature', 'used', 'limit', 'billing_link'],
    },
}


async def seed_email_system(db: AsyncSession) -> None:
    existing = await db.execute(select(EmailTemplate).limit(1))
    if existing.scalar_one_or_none():
        return

    slug_to_id: dict[str, object] = {}
    for slug, data in DEFAULT_TEMPLATES.items():
        tpl_id = uuid4()
        db.add(
            EmailTemplate(
                id=tpl_id,
                slug=slug,
                name=data['name'],
                subject=data['subject'],
                html_body=data['html'],
                variables=data['variables'],
                status='active',
                sender_name='TenderIQ',
                reply_to='support@tenderiq.com',
            )
        )
        slug_to_id[slug] = tpl_id

    for event_def in EVENT_REGISTRY:
        db.add(
            EmailEvent(
                id=uuid4(),
                event_key=event_def.event_key,
                name=event_def.name,
                category=event_def.category,
                description=event_def.description,
                template_id=slug_to_id.get(event_def.default_template_slug),
                is_enabled=True,
            )
        )

    db.add(
        EmailBranding(
            id=uuid4(),
            company_name='TenderIQ',
            primary_color='#2563eb',
            accent_color='#7c3aed',
            support_email='support@tenderiq.com',
        )
    )
    await db.commit()
    logger.info('Email system seeded')
