"""Build export payloads for tender analysis reports."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import AnalysisResult, Tender
from ..personal_workspace import get_company_profile_dict
from ..analysis_mapper import analysis_row_to_dashboard
from .section_format import format_dashboard_section, organization_line


async def build_tender_report_payload(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    tender_id: str,
    user_id: Optional[str] = None,
) -> dict[str, Any]:
    tender = await db.get(Tender, UUID(tender_id))
    q = (
        select(AnalysisResult)
        .where(
            AnalysisResult.tenant_id == tenant_id,
            AnalysisResult.tender_id == UUID(tender_id),
        )
        .order_by(AnalysisResult.created_at.desc())
        .limit(1)
    )
    row = (await db.execute(q)).scalar_one_or_none()
    dashboard = analysis_row_to_dashboard(tender_id, row)
    title = (tender.title if tender else None) or dashboard.get('title') or f'Tender Analysis'
    company = await get_company_profile_dict(db, user_id) if user_id else None
    org = organization_line(company)

    sections = []
    for key, label in (
        ('summary', 'Summary'),
        ('eligibility', 'Eligibility'),
        ('technical', 'Technical'),
        ('financial', 'Financial'),
        ('risks', 'Risks'),
        ('deadlines', 'Deadlines'),
        ('mandatoryDocs', 'Mandatory Documents'),
        ('mandatory_docs', 'Mandatory Documents'),
        ('importantClauses', 'Important Clauses'),
    ):
        value = dashboard.get(key)
        if value is None:
            continue
        content = format_dashboard_section(key, value)
        if not content.strip():
            continue
        if any(s['title'] == label for s in sections):
            continue
        sections.append({'title': label, 'content': content})

    summary_block = dashboard.get('summary') or {}
    summary_text = ''
    if isinstance(summary_block, dict):
        summary_text = str(summary_block.get('overallAssessment') or '')

    return {
        'title': title,
        'name': title,
        'status': dashboard.get('status', 'draft'),
        'organization': org,
        'created_at': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),
        'summary': summary_text,
        'sections': sections,
        'tender_id': tender_id,
        'metadata': dashboard,
        'company': company,
    }
