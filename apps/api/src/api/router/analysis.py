"""Analysis Results API — CRUD backed by AnalysisResult model."""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.models import AnalysisResult
from ...core.database import get_db
from ...core.tenant_utils import parse_tenant_uuid
from .analysis_dashboard import analysis_row_to_dashboard
from ..dependencies.rbac_deps import (
    RequireAiAnalysis,
    RequireAnalyticsView,
    require_tenant_member,
)

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
        'tender_id': str(r.tender_id) if r.tender_id else None,
        'bid_id': str(r.bid_id) if r.bid_id else None,
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


@router.get('/')
async def list_analysis(
    current_user: RequireAnalyticsView,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    tenant_uuid = parse_tenant_uuid(current_user.tenant_id)
    try:
        total_q = select(func.count(AnalysisResult.id)).where(AnalysisResult.tenant_id == tenant_uuid)
        total = await db.scalar(total_q) or 0

        q = (
            select(AnalysisResult)
            .where(AnalysisResult.tenant_id == tenant_uuid)
            .order_by(AnalysisResult.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        rows = (await db.execute(q)).scalars().all()
        return {'success': True, 'data': [_result_to_dict(r) for r in rows], 'total': total, 'page': page, 'limit': limit}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception('Failed to list analysis results')
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/by-tender/{tender_id}')
async def get_analysis_by_tender(
    tender_id: str,
    current_user: RequireAnalyticsView,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    tenant_uuid = parse_tenant_uuid(current_user.tenant_id)
    try:
        total_q = select(func.count(AnalysisResult.id)).where(
            AnalysisResult.tenant_id == tenant_uuid,
            AnalysisResult.tender_id == UUID(tender_id),
        )
        total = await db.scalar(total_q) or 0

        q = (
            select(AnalysisResult)
            .where(
                AnalysisResult.tenant_id == tenant_uuid,
                AnalysisResult.tender_id == UUID(tender_id),
            )
            .order_by(AnalysisResult.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        rows = (await db.execute(q)).scalars().all()
        return {'success': True, 'data': [_result_to_dict(r) for r in rows], 'total': total, 'page': page, 'limit': limit}
    except Exception as e:
        logger.exception('Failed to get analysis by tender')
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/tender/{tender_id}')
async def get_tender_dashboard_analysis(
    tender_id: str,
    current_user: RequireAnalyticsView,
    db: AsyncSession = Depends(get_db),
):
    """Dashboard-shaped analysis for a tender (latest result)."""
    tenant_uuid = parse_tenant_uuid(current_user.tenant_id)
    try:
        q = (
            select(AnalysisResult)
            .where(
                AnalysisResult.tenant_id == tenant_uuid,
                AnalysisResult.tender_id == UUID(tender_id),
            )
            .order_by(AnalysisResult.created_at.desc())
            .limit(1)
        )
        row = (await db.execute(q)).scalar_one_or_none()
        return {'success': True, 'data': analysis_row_to_dashboard(tender_id, row)}
    except Exception as e:
        logger.exception('Failed to get tender dashboard analysis')
        raise HTTPException(status_code=500, detail=str(e))


@router.patch('/tender/{tender_id}')
async def patch_tender_dashboard_analysis(
    tender_id: str,
    body: dict,
    current_user: RequireAiAnalysis,
    db: AsyncSession = Depends(get_db),
):
    tenant_uuid = parse_tenant_uuid(current_user.tenant_id)
    section = body.get('section')
    field_id = body.get('field_id')
    value = body.get('value')
    try:
        q = (
            select(AnalysisResult)
            .where(
                AnalysisResult.tenant_id == tenant_uuid,
                AnalysisResult.tender_id == UUID(tender_id),
            )
            .order_by(AnalysisResult.created_at.desc())
            .limit(1)
        )
        row = (await db.execute(q)).scalar_one_or_none()
        if not row:
            row = AnalysisResult(
                tenant_id=tenant_uuid,
                tender_id=UUID(tender_id),
                analysis_type='tender_summary',
                result=analysis_row_to_dashboard(tender_id, None),
            )
            db.add(row)

        dashboard = analysis_row_to_dashboard(tender_id, row)
        if section and field_id is not None:
            section_data = dashboard.get(section) if isinstance(dashboard.get(section), dict) else {}
            section_data = dict(section_data)
            section_data[str(field_id)] = value
            dashboard[section] = section_data
        row.result = dashboard
        await db.commit()
        await db.refresh(row)
        return {'success': True, 'data': dashboard}
    except Exception as e:
        await db.rollback()
        logger.exception('Failed to patch tender analysis')
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/', status_code=201)
async def create_analysis(
    body: dict,
    current_user: RequireAiAnalysis,
    db: AsyncSession = Depends(get_db),
):
    tenant_uuid = parse_tenant_uuid(current_user.tenant_id)
    try:
        obj = AnalysisResult(
            tenant_id=tenant_uuid,
            tender_id=UUID(body.get('tender_id')) if body.get('tender_id') else None,
            bid_id=UUID(body.get('bid_id')) if body.get('bid_id') else None,
            document_id=UUID(body.get('document_id')) if body.get('document_id') else None,
            analysis_type=body.get('analysis_type', 'tender_summary'),
            result=body.get('result', {}),
            summary=body.get('summary'),
            score=body.get('score'),
            confidence=body.get('confidence'),
            model_used=body.get('model_used'),
            tokens_used=body.get('tokens_used'),
            cost_usd=body.get('cost_usd'),
        )
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return {'success': True, 'data': _result_to_dict(obj)}
    except Exception as e:
        await db.rollback()
        logger.exception('Failed to create analysis result')
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/{analysis_id}')
async def get_analysis(
    analysis_id: str,
    current_user: RequireAnalyticsView,
    db: AsyncSession = Depends(get_db),
):
    tenant_uuid = parse_tenant_uuid(current_user.tenant_id)
    try:
        q = select(AnalysisResult).where(
            AnalysisResult.id == analysis_id,
            AnalysisResult.tenant_id == tenant_uuid,
        )
        row = (await db.execute(q)).scalar_one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail='Analysis result not found')
        return {'success': True, 'data': _result_to_dict(row)}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception('Failed to get analysis result')
        raise HTTPException(status_code=500, detail=str(e))


@router.delete('/{analysis_id}')
async def delete_analysis(
    analysis_id: str,
    current_user: RequireAiAnalysis,
    db: AsyncSession = Depends(get_db),
):
    tenant_uuid = parse_tenant_uuid(current_user.tenant_id)
    try:
        q = select(AnalysisResult).where(
            AnalysisResult.id == analysis_id,
            AnalysisResult.tenant_id == tenant_uuid,
        )
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
