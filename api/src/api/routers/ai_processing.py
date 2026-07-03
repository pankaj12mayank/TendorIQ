"""Phase 4 — AI catalog, test connection, document analysis."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.ai.lite_ai import (
    build_provider_catalog,
    catalog_to_dict,
    chat_completion,
    resolve_default_model,
    resolve_default_provider,
)
from ...core.database import get_db

from ...core.processing.document_analyzer import run_document_analysis
from ...core.processing.tasks import schedule_document_analysis
from ...core.billing.subscription_access import assert_can_use_system
from ...core.tenant_utils import parse_tenant_uuid
from ..dependencies.access import LiteUser, TenantUser
from ..schemas.base import create_response
from ..services.document_service import document_service
from ..services.file_service import file_service

router = APIRouter(tags=['AI & Processing'])


class AnalyzeDocumentBody(BaseModel):
    provider: Optional[str] = Field(None, description='openai | anthropic | gemini | ollama')
    model: Optional[str] = None
    async_mode: bool = Field(True, description='Return immediately and process in background')


class TestAIBody(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    prompt: str = 'Reply with JSON: {"ok": true, "message": "connected"}'


class FetchModelsBody(BaseModel):
    provider: str = Field(..., description='openai | anthropic | gemini | ollama')
    api_key: str = Field(..., description='API key for the provider')


@router.post('/ai/fetch-models')
async def fetch_ai_models(body: FetchModelsBody, _user: LiteUser):
    """Fetch available models from a provider using the given API key."""
    import httpx

    provider = body.provider.strip().lower()
    api_key = body.api_key.strip()

    if provider == 'openai':
        headers = {'Authorization': f'Bearer {api_key}'}
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get('https://api.openai.com/v1/models', headers=headers)
            if resp.status_code == 401:
                raise HTTPException(status_code=400, detail='Invalid API key')
            resp.raise_for_status()
            data = resp.json()
            models = sorted(
                [m['id'] for m in data.get('data', []) if not m['id'].startswith('ft:')],
            )
        return create_response({'provider': provider, 'models': models})

    elif provider == 'anthropic':
        headers = {
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
        }
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get('https://api.anthropic.com/v1/models', headers=headers)
            if resp.status_code == 401:
                raise HTTPException(status_code=400, detail='Invalid API key')
            resp.raise_for_status()
            data = resp.json()
            models = sorted([m['id'] for m in data.get('data', [])])
        return create_response({'provider': provider, 'models': models})

    elif provider == 'gemini':
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f'https://generativelanguage.googleapis.com/v1beta/models?key={api_key}',
            )
            if resp.status_code == 403:
                raise HTTPException(status_code=400, detail='Invalid API key')
            resp.raise_for_status()
            data = resp.json()
            models = sorted(
                [m['name'].replace('models/', '') for m in data.get('models', [])]
            )
        return create_response({'provider': provider, 'models': models})

    elif provider == 'ollama':
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                resp = await client.get(f'{api_key}/api/tags')
                resp.raise_for_status()
                data = resp.json()
                models = sorted([m['name'] for m in data.get('models', [])])
            except Exception:
                models = []
        return create_response({'provider': provider, 'models': models})

    raise HTTPException(status_code=400, detail=f'Unknown provider: {provider}')


@router.get('/ai/catalog')
async def get_ai_catalog(_user: LiteUser):
    """List configured AI providers and available models."""
    providers = await build_provider_catalog()
    return create_response(catalog_to_dict(providers))


@router.post('/ai/test')
async def test_ai_connection(body: TestAIBody, _user: LiteUser):
    """Verify provider key and model respond."""
    try:
        result = await chat_completion(
            [{'role': 'user', 'content': body.prompt}],
            provider=body.provider,
            model=body.model,
            max_tokens=256,
            json_mode=True,
        )
        return create_response(
            {
                'ok': True,
                'provider': result['provider'],
                'model': result['model'],
                'preview': (result.get('content') or '')[:500],
            }
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get('/processing/documents/{document_id}')
async def get_processing_status(
    document_id: str,
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
):
    is_admin = current_user.is_super_admin()
    if not is_admin:
        if not current_user.tenant_id:
            raise HTTPException(status_code=400, detail='Workspace context required')
        await assert_can_use_system(db, parse_tenant_uuid(current_user.tenant_id))

    tenant_uuid = parse_tenant_uuid(current_user.tenant_id) if current_user.tenant_id else None
    doc = await file_service.get_document(db, UUID(document_id), tenant_id=tenant_uuid)
    if not doc:
        raise HTTPException(status_code=404, detail='Document not found')

    meta = doc.metadata_json or {}
    analysis_meta = meta.get('analysis') or {}
    return create_response(
        {
            'document_id': document_id,
            'processing_status': doc.processing_status,
            'processing_error': doc.processing_error,
            'tender_id': str(doc.tender_id) if doc.tender_id else None,
            'analysis': analysis_meta,
            'default_provider': resolve_default_provider(),
            'default_model': resolve_default_model(resolve_default_provider()),
        }
    )


@router.post('/processing/documents/{document_id}/analyze')
async def analyze_document(
    document_id: str,
    body: AnalyzeDocumentBody,
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
):
    """Run (or re-run) AI analysis on an uploaded document."""
    is_admin = current_user.is_super_admin()
    if not is_admin:
        if not current_user.tenant_id:
            raise HTTPException(status_code=400, detail='Workspace context required')
        await assert_can_use_system(db, parse_tenant_uuid(current_user.tenant_id))

    tenant_uuid = parse_tenant_uuid(current_user.tenant_id) if current_user.tenant_id else None
    if is_admin and not tenant_uuid:
        doc_ref = await file_service.get_document(db, UUID(document_id), tenant_id=None)
        if doc_ref and doc_ref.tenant_id:
            tenant_uuid = doc_ref.tenant_id

    doc = await file_service.get_document(db, UUID(document_id), tenant_id=tenant_uuid)
    if not doc:
        raise HTTPException(status_code=404, detail='Document not found')

    if body.async_mode:
        await schedule_document_analysis(
            document_id=document_id,
            tenant_id=str(tenant_uuid),
            owner_id=current_user.user_id,
            provider=body.provider,
            model=body.model,
            force=True,
        )
        return create_response(
            {
                'success': True,
                'document_id': document_id,
                'processing_status': 'processing',
                'message': 'Analysis started',
            }
        )

    try:
        result = await run_document_analysis(
            db,
            document_id=UUID(document_id),
            tenant_id=tenant_uuid,
            owner_id=UUID(current_user.user_id),
            provider=body.provider,
            model=body.model,
        )
        return create_response(result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post('/processing/documents/{document_id}/retry')
async def retry_document_analysis(
    document_id: str,
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
    provider: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
):
    """Retry failed analysis (increments retry_count)."""
    is_admin = current_user.is_super_admin()
    if not is_admin:
        if not current_user.tenant_id:
            raise HTTPException(status_code=400, detail='Workspace context required')
        await assert_can_use_system(db, parse_tenant_uuid(current_user.tenant_id))

    tenant_uuid = parse_tenant_uuid(current_user.tenant_id) if current_user.tenant_id else None
    if is_admin and not tenant_uuid:
        doc = await file_service.get_document(db, UUID(document_id), tenant_id=None)
        if doc and doc.tenant_id:
            tenant_uuid = doc.tenant_id
    if not tenant_uuid:
        raise HTTPException(status_code=400, detail='Workspace context required')

    doc = await document_service.retry_document(db, UUID(document_id), tenant_uuid)
    if not doc:
        raise HTTPException(status_code=404, detail='Document not found or max retries exceeded')

    await schedule_document_analysis(
        document_id=document_id,
        tenant_id=str(tenant_uuid),
        owner_id=current_user.user_id,
        provider=provider,
        model=model,
        force=True,
    )
    return create_response(
        {
            'success': True,
            'document_id': document_id,
            'retry_count': doc.retry_count,
            'processing_status': doc.processing_status,
        }
    )
