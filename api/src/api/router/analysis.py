"""Analysis Results API — user-scoped CRUD."""

import logging
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.models import AnalysisResult
from ...core.database import get_db
from ...core.lite_scope import apply_user_scope, parse_user_uuid, user_owns_row
from ...core.billing.subscription_access import assert_can_use_system
from ...core.tenant_utils import parse_tenant_uuid
from ...core.analysis_mapper import analysis_row_to_dashboard
from ..dependencies.access import TenantUser, require_tenant_member
from ..schemas.base import create_paginated_response, create_response

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix='/analysis',
    tags=['Analysis'],
    dependencies=[Depends(require_tenant_member)],
)


def _result_to_dict(r: AnalysisResult) -> dict:
    return {
        'id': str(r.id),
        'tenant_id': str(r.tenant_id),
        'owner_id': str(r.owner_id) if r.owner_id else None,
        'tender_id': str(r.tender_id) if r.tender_id else None,
        'document_id': str(r.document_id) if r.document_id else None,
        'analysis_type': r.analysis_type,
        'result': r.result,
        'summary': r.summary,
        'score': r.score,
        'confidence': r.confidence,
        'model_used': r.model_used,
        'tokens_used': r.tokens_used,
        'cost_usd': r.cost_usd,
        'created_at': r.created_at.isoformat() if r.created_at else None,
    }


def _scoped_select(current_user: TenantUser, tender_id: Optional[str] = None):
    q = select(AnalysisResult)
    if tender_id:
        q = q.where(AnalysisResult.tender_id == UUID(tender_id))
    return apply_user_scope(q, AnalysisResult, current_user)


@router.get('/')
async def list_analysis(
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    if current_user.tenant_id:
        await assert_can_use_system(db, parse_tenant_uuid(current_user.tenant_id))
    try:
        count_q = apply_user_scope(select(func.count(AnalysisResult.id)), AnalysisResult, current_user)
        total = await db.scalar(count_q) or 0

        q = (
            _scoped_select(current_user)
            .order_by(AnalysisResult.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        rows = (await db.execute(q)).scalars().all()
        return create_paginated_response(
            [_result_to_dict(r) for r in rows],
            page=page,
            limit=limit,
            total=total,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception('Failed to list analysis results')
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/by-tender/{tender_id}')
async def get_analysis_by_tender(
    tender_id: str,
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    if current_user.tenant_id:
        await assert_can_use_system(db, parse_tenant_uuid(current_user.tenant_id))
    try:
        count_q = apply_user_scope(
            select(func.count(AnalysisResult.id)).where(AnalysisResult.tender_id == UUID(tender_id)),
            AnalysisResult,
            current_user,
        )
        total = await db.scalar(count_q) or 0

        q = (
            _scoped_select(current_user, tender_id)
            .order_by(AnalysisResult.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        rows = (await db.execute(q)).scalars().all()
        return create_paginated_response(
            [_result_to_dict(r) for r in rows],
            page=page,
            limit=limit,
            total=total,
        )
    except Exception as e:
        logger.exception('Failed to get analysis by tender')
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/tender/{tender_id}')
async def get_tender_dashboard_analysis(
    tender_id: str,
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
):
    if current_user.tenant_id:
        await assert_can_use_system(db, parse_tenant_uuid(current_user.tenant_id))
    """Dashboard-shaped analysis for a tender (latest result)."""
    try:
        q = (
            _scoped_select(current_user, tender_id)
            .order_by(AnalysisResult.created_at.desc())
            .limit(1)
        )
        row = (await db.execute(q)).scalar_one_or_none()
        return create_response(analysis_row_to_dashboard(tender_id, row))
    except Exception as e:
        logger.exception('Failed to get tender dashboard analysis')
        raise HTTPException(status_code=500, detail=str(e))


class PatchAnalysisBody(BaseModel):
    section: Optional[str] = None
    field_id: Optional[str] = None
    value: Any = None


@router.patch('/tender/{tender_id}')
async def patch_tender_dashboard_analysis(
    tender_id: str,
    body: PatchAnalysisBody,
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
):
    if current_user.tenant_id:
        await assert_can_use_system(db, parse_tenant_uuid(current_user.tenant_id))
    tenant_uuid = parse_tenant_uuid(current_user.tenant_id)
    owner_uuid = parse_user_uuid(current_user.user_id)
    section = body.section
    field_id = body.field_id
    value = body.value
    try:
        q = (
            _scoped_select(current_user, tender_id)
            .order_by(AnalysisResult.created_at.desc())
            .limit(1)
        )
        row = (await db.execute(q)).scalar_one_or_none()
        if not row:
            row = AnalysisResult(
                tenant_id=tenant_uuid,
                owner_id=owner_uuid,
                tender_id=UUID(tender_id),
                analysis_type='tender_summary',
                result=analysis_row_to_dashboard(tender_id, None),
            )
            db.add(row)
        elif not user_owns_row(row, current_user.user_id) and not current_user.is_super_admin():
            raise HTTPException(status_code=403, detail='Access denied')

        dashboard = analysis_row_to_dashboard(tender_id, row)
        if section and field_id is not None:
            section_data = dashboard.get(section) if isinstance(dashboard.get(section), dict) else {}
            section_data = dict(section_data)
            section_data[str(field_id)] = value
            dashboard[section] = section_data
        row.result = dashboard
        if not row.owner_id:
            row.owner_id = owner_uuid
        await db.commit()
        await db.refresh(row)
        return create_response(dashboard)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception('Failed to patch tender analysis')
        raise HTTPException(status_code=500, detail=str(e))


class CreateAnalysisBody(BaseModel):
    tender_id: str = Field(..., min_length=1)
    document_id: Optional[str] = None
    analysis_type: str = 'tender_summary'
    result: Optional[dict] = None
    summary: Optional[str] = None
    score: Optional[float] = None
    confidence: Optional[float] = None
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None


@router.post('/', status_code=201)
async def create_analysis(
    body: CreateAnalysisBody,
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
):
    if current_user.tenant_id:
        await assert_can_use_system(db, parse_tenant_uuid(current_user.tenant_id))
    tenant_uuid = parse_tenant_uuid(current_user.tenant_id)
    try:
        obj = AnalysisResult(
            tenant_id=tenant_uuid,
            owner_id=parse_user_uuid(current_user.user_id),
            tender_id=UUID(body.tender_id) if body.tender_id else None,
            document_id=UUID(body.document_id) if body.document_id else None,
            analysis_type=body.analysis_type,
            result=body.result or {},
            summary=body.summary,
            score=body.score,
            confidence=body.confidence,
            model_used=body.model_used,
            tokens_used=body.tokens_used,
            cost_usd=body.cost_usd,
        )
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return create_response(_result_to_dict(obj))
    except Exception as e:
        await db.rollback()
        logger.exception('Failed to create analysis result')
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/{analysis_id}')
async def get_analysis(
    analysis_id: str,
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
):
    if current_user.tenant_id:
        await assert_can_use_system(db, parse_tenant_uuid(current_user.tenant_id))
    try:
        q = _scoped_select(current_user).where(AnalysisResult.id == analysis_id)
        row = (await db.execute(q)).scalar_one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail='Analysis result not found')
        return create_response(_result_to_dict(row))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception('Failed to get analysis result')
        raise HTTPException(status_code=500, detail=str(e))


@router.delete('/{analysis_id}')
async def delete_analysis(
    analysis_id: str,
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
):
    if current_user.tenant_id:
        await assert_can_use_system(db, parse_tenant_uuid(current_user.tenant_id))
    try:
        q = _scoped_select(current_user).where(AnalysisResult.id == analysis_id)
        row = (await db.execute(q)).scalar_one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail='Analysis result not found')
        await db.delete(row)
        await db.commit()
        return {'success': True, 'message': 'Analysis result deleted'}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception('Failed to delete analysis result')
        raise HTTPException(status_code=500, detail=str(e))
