"""Lite proposal generation — DB-backed, multi-provider AI, company profile."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..ai.lite_ai import chat_completion, extract_json_object, resolve_default_model, resolve_default_provider
from ..models import AnalysisResult, CompanyProfile, Proposal, Tender
from ..proposal.prompts import ProposalPrompts
from ..proposal.schemas import SectionType
from ..analysis_mapper import analysis_row_to_dashboard

logger = logging.getLogger(__name__)

SECTION_ORDER = [
    SectionType.EXECUTIVE_SUMMARY,
    SectionType.COMPANY_PROFILE,
    SectionType.UNDERSTANDING,
    SectionType.APPROACH,
    SectionType.TEAM,
    SectionType.TIMELINE,
]

PROMPTS = {
    SectionType.EXECUTIVE_SUMMARY: ProposalPrompts.EXECUTIVE_SUMMARY_PROMPT,
    SectionType.COMPANY_PROFILE: ProposalPrompts.COMPANY_PROFILE_PROMPT,
    SectionType.UNDERSTANDING: ProposalPrompts.UNDERSTANDING_PROMPT,
    SectionType.APPROACH: ProposalPrompts.APPROACH_PROMPT,
    SectionType.TEAM: ProposalPrompts.TEAM_PROMPT,
    SectionType.TIMELINE: ProposalPrompts.TIMELINE_PROMPT,
}


def company_profile_to_text(profile: Optional[dict]) -> str:
    if not profile:
        return 'Company details not configured. Add company profile in Settings.'
    parts = [
        f"Company: {profile.get('company_name') or 'N/A'}",
        f"Industry: {profile.get('industry') or 'N/A'}",
        f"Address: {profile.get('address') or 'N/A'}",
        f"Phone: {profile.get('phone') or 'N/A'}",
        f"Website: {profile.get('website') or 'N/A'}",
        f"Tax ID: {profile.get('tax_id') or 'N/A'}",
    ]
    return '\n'.join(parts)


def dashboard_to_tender_text(dashboard: dict[str, Any]) -> str:
    lines = [f"Status: {dashboard.get('status', 'unknown')}"]
    summary = dashboard.get('summary') or {}
    if isinstance(summary, dict):
        lines.append(f"Assessment: {summary.get('overallAssessment', '')}")
        for finding in summary.get('keyFindings') or []:
            lines.append(f"- {finding}")
    for key in ('eligibility', 'technical', 'financial', 'risks', 'deadlines', 'importantClauses'):
        block = dashboard.get(key)
        if block:
            lines.append(f"\n## {key}\n{block}")
    return '\n'.join(lines)[:12000]


async def fetch_tender_analysis_text(
    db: AsyncSession, tender_id: UUID, tenant_id: UUID
) -> str:
    q = (
        select(AnalysisResult)
        .where(
            AnalysisResult.tenant_id == tenant_id,
            AnalysisResult.tender_id == tender_id,
        )
        .order_by(AnalysisResult.created_at.desc())
        .limit(1)
    )
    row = (await db.execute(q)).scalar_one_or_none()
    dashboard = analysis_row_to_dashboard(str(tender_id), row)
    return dashboard_to_tender_text(dashboard)


async def generate_section_content(
    section_type: SectionType,
    tender_text: str,
    company_text: str,
    *,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    style: str = 'professional',
) -> dict[str, Any]:
    template = PROMPTS.get(section_type)
    if not template:
        return {'title': section_type.value.replace('_', ' ').title(), 'content': ''}

    user_content = template.format(
        tender_info=tender_text[:5000],
        company_profile=company_text[:2000],
        tender_requirements=tender_text[:5000],
        technical_requirements=tender_text[:5000],
        tender_timeline=tender_text[:3000],
        tender_terms=tender_text[:3000],
        company_info=company_text[:2000],
        experience=company_text[:2000],
        team_info=company_text[:2000],
        pricing_info=tender_text[:2000],
    )
    user_content += f"\n\nWriting style: {style}. Return ONLY valid JSON."

    result = await chat_completion(
        [
            {'role': 'system', 'content': ProposalPrompts.SYSTEM_PROMPT},
            {'role': 'user', 'content': user_content},
        ],
        provider=provider,
        model=model,
        temperature=0.5,
        max_tokens=4096,
        json_mode=True,
    )
    try:
        return extract_json_object(result['content'])
    except Exception as exc:
        logger.warning('Section %s JSON parse failed: %s', section_type, exc)
        return {
            'title': section_type.value.replace('_', ' ').title(),
            'content': result.get('content', '')[:8000],
        }


def proposal_row_to_dict(row: Proposal) -> dict[str, Any]:
    payload = row.sections_json if isinstance(row.sections_json, dict) else {}
    return {
        'id': str(row.id),
        'tender_id': str(row.tender_id),
        'title': row.title or payload.get('title') or 'Tender Proposal',
        'status': row.status,
        'sections': payload.get('sections', []),
        'total_words': payload.get('total_words', 0),
        'estimated_pages': payload.get('estimated_pages', 1),
        'model_used': row.model_used,
        'updated_at': row.updated_at.isoformat() if row.updated_at else None,
        'generation': payload.get('generation', {}),
    }


async def get_proposal_for_tender(
    db: AsyncSession,
    tender_id: UUID,
    owner_id: UUID,
) -> Optional[Proposal]:
    q = (
        select(Proposal)
        .where(Proposal.tender_id == tender_id, Proposal.owner_id == owner_id)
        .order_by(Proposal.updated_at.desc())
        .limit(1)
    )
    return (await db.execute(q)).scalar_one_or_none()


async def generate_proposal_for_tender(
    db: AsyncSession,
    *,
    tender_id: UUID,
    tenant_id: UUID,
    owner_id: UUID,
    company_profile: Optional[dict],
    provider: Optional[str] = None,
    model: Optional[str] = None,
    style: str = 'professional',
    tone: str = 'formal',
) -> dict[str, Any]:
    tender = await db.get(Tender, tender_id)
    if not tender or tender.tenant_id != tenant_id:
        raise ValueError('Tender not found')

    from ..billing.lite_usage import enforce_quota, track_usage

    await enforce_quota(db, tenant_id, 'proposal_generate')

    prov = provider or resolve_default_provider()
    mdl = model or resolve_default_model(prov)
    company_text = company_profile_to_text(company_profile)
    tender_text = await fetch_tender_analysis_text(db, tender_id, tenant_id)
    if len(tender_text) < 80:
        raise ValueError(
            'No analysis found for this tender. '
            'Run document analysis first before generating a proposal.'
        )

    sections_out: list[dict[str, Any]] = []
    total_words = 0
    warnings: list[str] = []

    for idx, section_type in enumerate(SECTION_ORDER):
        try:
            data = await generate_section_content(
                section_type,
                tender_text,
                company_text,
                provider=prov,
                model=mdl,
                style=style,
            )
            content = data.get('content', '') or ''
            section = {
                'section_id': str(uuid4()),
                'section_type': section_type.value,
                'title': data.get('title') or section_type.value.replace('_', ' ').title(),
                'content': content,
                'order': idx,
                'word_count': len(content.split()),
                'is_generated': True,
            }
            sections_out.append(section)
            total_words += section['word_count']
        except Exception as exc:
            logger.warning('Proposal section %s failed: %s', section_type, exc)
            warnings.append(str(section_type.value))

    title = f"Proposal — {tender.title}"[:500]
    payload = {
        'title': title,
        'sections': sections_out,
        'total_words': total_words,
        'estimated_pages': max(1, total_words // 300),
        'tone': tone,
        'style': style,
        'generation': {
            'provider': prov,
            'model': mdl,
            'warnings': warnings,
            'completed_at': datetime.now(timezone.utc).isoformat(),
        },
    }

    existing = await get_proposal_for_tender(db, tender_id, owner_id)
    if existing:
        existing.title = title
        existing.sections_json = payload
        existing.status = 'completed'
        existing.model_used = f'{prov}:{mdl}'
        existing.description = (sections_out[0]['content'][:500] if sections_out else None)
        existing.updated_at = datetime.now(timezone.utc)
        row = existing
    else:
        row = Proposal(
            tenant_id=tenant_id,
            owner_id=owner_id,
            created_by_id=owner_id,
            tender_id=tender_id,
            bidder_id=owner_id,
            title=title,
            sections_json=payload,
            status='completed',
            model_used=f'{prov}:{mdl}',
            description=(sections_out[0]['content'][:500] if sections_out else None),
        )
        db.add(row)

    await track_usage(
        db,
        tenant_id=tenant_id,
        user_id=owner_id,
        action='proposal_generate',
        resource_type='proposal',
        resource_id=row.id,
    )
    await db.commit()
    await db.refresh(row)
    out = proposal_row_to_dict(row)
    out['warnings'] = warnings
    return out


def build_proposal_pdf_data(proposal: dict[str, Any], company: Optional[dict]) -> dict[str, Any]:
    org_parts = []
    if company:
        if company.get('company_name'):
            org_parts.append(company['company_name'])
        if company.get('address'):
            org_parts.append(company['address'])
        if company.get('phone'):
            org_parts.append(f"Tel: {company['phone']}")
        if company.get('website'):
            org_parts.append(company['website'])
    return {
        'title': proposal.get('title', 'Proposal'),
        'status': proposal.get('status', 'draft'),
        'organization': ' | '.join(org_parts) if org_parts else None,
        'created_at': proposal.get('updated_at'),
        'sections': [
            {
                'title': s.get('title', ''),
                'content': s.get('content', ''),
                'word_count': s.get('word_count', 0),
            }
            for s in proposal.get('sections', [])
        ],
        'summary': proposal.get('sections', [{}])[0].get('content', '')[:500]
        if proposal.get('sections')
        else '',
    }
