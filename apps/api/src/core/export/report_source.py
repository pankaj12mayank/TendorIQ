"""Build export payloads for tender analysis reports."""

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import AnalysisResult
from ...api.router.analysis_dashboard import analysis_row_to_dashboard


async def build_tender_report_payload(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    tender_id: str,
) -> dict[str, Any]:
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
    title = dashboard.get('title') or f'Tender Analysis {tender_id}'
    sections = []
    for key, label in (
        ('summary', 'Summary'),
        ('eligibility', 'Eligibility'),
        ('technical', 'Technical'),
        ('financial', 'Financial'),
        ('risks', 'Risks'),
        ('deadlines', 'Deadlines'),
        ('mandatory_docs', 'Mandatory Documents'),
    ):
        value = dashboard.get(key)
        if value is None:
            continue
        if isinstance(value, dict):
            content = value.get('content') or value.get('summary') or str(value)
        else:
            content = str(value)
        sections.append({'title': label, 'content': content})

    return {
        'title': title,
        'name': title,
        'status': dashboard.get('status', 'draft'),
        'summary': dashboard.get('summary', {}).get('content')
        if isinstance(dashboard.get('summary'), dict)
        else str(dashboard.get('summary', '')),
        'sections': sections,
        'tender_id': tender_id,
        'metadata': dashboard,
    }
