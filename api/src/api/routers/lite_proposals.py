"""Lite proposals — DB-backed generation with company profile + multi-provider AI."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.export.pdf_generator import get_pdf_generator
from ...core.lite_scope import apply_user_scope, user_owns_row
from ...core.models import Proposal
from ...core.personal_workspace import get_ai_preferences_dict, get_company_profile_dict
from ...core.proposal.lite_service import (
    build_proposal_pdf_data,
    generate_proposal_for_tender,
    get_proposal_for_tender,
    proposal_row_to_dict,
)
from ..dependencies.access import LiteUser, TenantUser, require_tenant_member
from ..schemas.base import create_response
from sqlalchemy import select

router = APIRouter(
    prefix='/proposals',
    tags=['proposals'],
    dependencies=[Depends(require_tenant_member)],
)


class GenerateProposalBody(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    style: str = 'professional'
    tone: str = 'formal'


class UpdateProposalSectionBody(BaseModel):
    content: str = Field(..., min_length=1)


class ProposalAutosaveBody(BaseModel):
    title: Optional[str] = None
    sections: list[dict] = Field(default_factory=list)


@router.get('/tender/{tender_id}')
async def get_tender_proposal(
    tender_id: str,
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
):
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Workspace context required')
    row = await get_proposal_for_tender(
        db, UUID(tender_id), UUID(current_user.user_id)
    )
    if not row:
        return create_response(None)
    if not user_owns_row(row, current_user.user_id):
        raise HTTPException(status_code=403, detail='Access denied')
    return create_response(proposal_row_to_dict(row))


@router.post('/tender/{tender_id}/generate')
async def generate_tender_proposal(
    tender_id: str,
    body: GenerateProposalBody,
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
):
    from ...core.billing.lite_usage import enforce_quota
    from ...core.billing.subscription_access import assert_can_use_system
    from ...core.tenant_utils import resolve_member_tenant_uuid

    tenant_uuid = await resolve_member_tenant_uuid(current_user, db)
    await assert_can_use_system(
        db, tenant_uuid, is_super_admin=current_user.is_super_admin()
    )
    await enforce_quota(db, tenant_uuid, 'proposal_generate')
    current_user.tenant_id = str(tenant_uuid)

    prefs = await get_ai_preferences_dict(db, current_user.user_id)
    company = await get_company_profile_dict(db, current_user.user_id)
    provider = body.provider or prefs.get('provider')
    model = body.model or prefs.get('model')
    style = body.style or prefs.get('style') or 'professional'

    try:
        result = await generate_proposal_for_tender(
            db,
            tender_id=UUID(tender_id),
            tenant_id=UUID(current_user.tenant_id),
            owner_id=UUID(current_user.user_id),
            company_profile=company,
            provider=provider,
            model=model,
            style=style,
            tone=body.tone or prefs.get('tone') or 'formal',
        )
        return create_response(result)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get('/{proposal_id}')
async def get_proposal_by_id(
    proposal_id: str,
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
):
    q = apply_user_scope(select(Proposal), Proposal, current_user).where(
        Proposal.id == UUID(proposal_id)
    )
    row = (await db.execute(q)).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail='Proposal not found')
    return create_response(proposal_row_to_dict(row))


@router.patch('/{proposal_id}/sections/{section_id}')
async def update_proposal_section(
    proposal_id: str,
    section_id: str,
    body: UpdateProposalSectionBody,
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
):
    q = apply_user_scope(select(Proposal), Proposal, current_user).where(
        Proposal.id == UUID(proposal_id)
    )
    row = (await db.execute(q)).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail='Proposal not found')

    payload = dict(row.sections_json or {})
    sections = payload.get('sections') or []
    found = False
    for section in sections:
        if section.get('section_id') == section_id:
            section['content'] = body.content
            section['word_count'] = len(body.content.split())
            section['is_edited'] = True
            found = True
            break
    if not found:
        raise HTTPException(status_code=404, detail='Section not found')

    payload['sections'] = sections
    row.sections_json = payload
    await db.commit()
    await db.refresh(row)
    return create_response(proposal_row_to_dict(row))


@router.patch('/{proposal_id}/autosave')
async def autosave_proposal(
    proposal_id: str,
    body: ProposalAutosaveBody,
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
):
    q = apply_user_scope(select(Proposal), Proposal, current_user).where(
        Proposal.id == UUID(proposal_id)
    )
    row = (await db.execute(q)).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail='Proposal not found')

    payload = dict(row.sections_json or {})
    incoming = body.sections or []
    payload['sections'] = incoming
    payload['total_words'] = sum(len(str(s.get('content') or '').split()) for s in incoming)
    payload['estimated_pages'] = max(1, payload['total_words'] // 300)
    payload['autosaved_at'] = datetime.utcnow().isoformat()
    if body.title:
        row.title = body.title[:500]
        payload['title'] = row.title
    row.sections_json = payload
    row.status = 'draft'
    await db.commit()
    await db.refresh(row)
    return create_response(proposal_row_to_dict(row))


@router.post('/{proposal_id}/export/pdf')
async def export_proposal_pdf(
    proposal_id: str,
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
):
    q = apply_user_scope(select(Proposal), Proposal, current_user).where(
        Proposal.id == UUID(proposal_id)
    )
    row = (await db.execute(q)).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail='Proposal not found')

    from ...core.billing.lite_usage import enforce_quota, track_usage
    from ...core.billing.subscription_access import assert_can_use_system
    from ...core.tenant_utils import resolve_member_tenant_uuid

    tenant_uuid = await resolve_member_tenant_uuid(current_user, db)
    await assert_can_use_system(
        db, tenant_uuid, is_super_admin=current_user.is_super_admin()
    )
    await enforce_quota(db, tenant_uuid, 'export_pdf')
    current_user.tenant_id = str(tenant_uuid)

    company = await get_company_profile_dict(db, current_user.user_id)
    proposal_dict = proposal_row_to_dict(row)
    pdf_data = build_proposal_pdf_data(proposal_dict, company)
    pdf_bytes = get_pdf_generator().generate_proposal_pdf(pdf_data)
    await track_usage(
        db,
        tenant_id=UUID(current_user.tenant_id),
        user_id=UUID(current_user.user_id),
        action='export',
        resource_type='proposal',
        resource_id=UUID(proposal_id),
        metadata={'format': 'pdf'},
    )
    await db.commit()
    filename = f"proposal-{proposal_id[:8]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )
