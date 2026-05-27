"""Phase 4 — upload → extract text → AI → store dashboard analysis."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..ai.lite_ai import chat_completion, extract_json_object, resolve_default_model, resolve_default_provider
from ...api.router.analysis_mapper import empty_dashboard_analysis
from ..config import settings
from ..models import AnalysisResult, Document, Tender
from ..parsers.parser import parser_service
from ..storage.client import storage_service

logger = logging.getLogger(__name__)

MAX_TEXT_CHARS = 100_000

ANALYSIS_SYSTEM = """You are a tender document analyst. Extract structured insights from the document text.
Return ONLY valid JSON matching this schema (no markdown):
{
  "summary": {
    "confidence": {"value": 0.0-1.0, "label": "Low|Medium|High"},
    "keyFindings": ["string"],
    "overallAssessment": "string"
  },
  "eligibility": {"overallScore": 0-100, "criteria": [{"id": "string", "name": "string", "met": bool, "notes": "string"}]},
  "technical": {"complianceRate": 0-100, "requirements": [{"id": "string", "title": "string", "status": "compliant|partial|missing", "detail": "string"}]},
  "financial": {"totalValue": number, "currency": "USD", "items": [{"label": "string", "amount": number, "notes": "string"}]},
  "risks": {"overallRiskScore": 0-100, "risks": [{"id": "string", "title": "string", "severity": "low|medium|high", "mitigation": "string"}]},
  "deadlines": {"deadlines": [{"id": "string", "label": "string", "date": "ISO8601 or descriptive", "critical": bool}]},
  "mandatoryDocs": {"overallCompletion": 0-100, "documents": [{"name": "string", "required": bool, "status": "present|missing|unknown"}]},
  "importantClauses": {"clauses": [{"id": "string", "title": "string", "excerpt": "string", "impact": "string", "category": "legal|commercial|technical|other"}]}
}
Use realistic values inferred from the document. If information is missing, use conservative defaults and note gaps in keyFindings."""


def _merge_dashboard(tender_id: str, ai_payload: dict[str, Any]) -> dict[str, Any]:
    base = empty_dashboard_analysis(tender_id)
    base['status'] = 'completed'
    for key in (
        'summary',
        'eligibility',
        'technical',
        'financial',
        'risks',
        'deadlines',
        'mandatoryDocs',
        'importantClauses',
    ):
        if key in ai_payload and isinstance(ai_payload[key], dict):
            base[key] = {**base.get(key, {}), **ai_payload[key]}
    return base


async def _ensure_tender(
    db: AsyncSession,
    doc: Document,
    owner_id: UUID,
) -> Tender:
    if doc.tender_id:
        tender = await db.get(Tender, doc.tender_id)
        if tender:
            return tender

    title = (doc.name or doc.file_name or 'Uploaded tender')[:500]
    tender = Tender(
        tenant_id=doc.tenant_id,
        owner_id=owner_id,
        created_by_id=owner_id,
        title=title,
        description=f'Auto-created from document: {doc.file_name}',
        status='draft',
    )
    db.add(tender)
    await db.flush()
    doc.tender_id = tender.id
    await db.flush()
    return tender


async def run_document_analysis(
    db: AsyncSession,
    *,
    document_id: UUID,
    tenant_id: UUID,
    owner_id: UUID,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> dict[str, Any]:
    """Parse document, call AI, persist AnalysisResult. Returns status dict."""
    doc = await db.get(Document, document_id)
    if not doc or doc.tenant_id != tenant_id:
        raise ValueError('Document not found')

    from ..billing.lite_usage import enforce_quota, track_usage

    await enforce_quota(db, tenant_id, 'ai_analysis')

    prov = provider or resolve_default_provider()
    mdl = model or resolve_default_model(prov)

    doc.processing_status = 'processing'
    doc.processing_error = None
    meta = dict(doc.metadata_json or {})
    meta['analysis'] = {
        'status': 'running',
        'provider': prov,
        'model': mdl,
        'started_at': datetime.now(timezone.utc).isoformat(),
    }
    doc.metadata_json = meta
    await db.commit()

    try:
        read = await storage_service.read_file(doc.storage_key)
        if not read.get('success') or not read.get('content'):
            raise ValueError(read.get('error') or 'Could not read file from storage')

        file_bytes = read['content']
        parsed, _chunks = await parser_service.parse(
            file_bytes,
            doc.file_name or doc.name,
            str(document_id),
            chunk=False,
        )
        text = (parsed.full_text or '').strip()
        if not text:
            raise ValueError('No extractable text in document (try a text-based PDF or DOCX)')

        if len(text) > MAX_TEXT_CHARS:
            text = text[:MAX_TEXT_CHARS] + '\n\n[truncated for analysis]'

        tender = await _ensure_tender(db, doc, owner_id)
        tender_id = str(tender.id)

        user_prompt = f"""Analyze this tender document.

File: {doc.file_name}
Type: {doc.file_type}

--- DOCUMENT TEXT ---
{text}
--- END ---"""

        completion = await chat_completion(
            [
                {'role': 'system', 'content': ANALYSIS_SYSTEM},
                {'role': 'user', 'content': user_prompt},
            ],
            provider=prov,
            model=mdl,
            temperature=min(settings.AI_TEMPERATURE, 0.4),
            max_tokens=settings.AI_MAX_TOKENS,
            json_mode=True,
        )

        ai_json = extract_json_object(completion['content'])
        dashboard = _merge_dashboard(tender_id, ai_json)
        dashboard['tenderId'] = tender_id
        dashboard['documentId'] = str(document_id)
        dashboard['ai'] = {
            'provider': completion['provider'],
            'model': completion['model'],
            'usage': completion.get('usage', {}),
        }

        usage = completion.get('usage') or {}
        tokens = int(usage.get('input_tokens', 0)) + int(usage.get('output_tokens', 0))
        confidence = None
        summary_block = dashboard.get('summary') or {}
        conf = summary_block.get('confidence') if isinstance(summary_block, dict) else None
        if isinstance(conf, dict) and conf.get('value') is not None:
            confidence = float(conf['value'])

        existing_row = (
            await db.execute(
                select(AnalysisResult)
                .where(
                    AnalysisResult.tenant_id == tenant_id,
                    AnalysisResult.document_id == document_id,
                    AnalysisResult.analysis_type == 'tender_dashboard',
                )
                .order_by(AnalysisResult.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if existing_row:
            row = existing_row
            row.owner_id = owner_id
            row.tender_id = tender.id
            row.result = dashboard
            row.summary = summary_block.get('overallAssessment') if isinstance(summary_block, dict) else None
            row.score = float((dashboard.get('eligibility') or {}).get('overallScore') or 0)
            row.confidence = confidence
            row.model_used = f"{completion['provider']}:{completion['model']}"
            row.tokens_used = tokens or None
        else:
            row = AnalysisResult(
                tenant_id=tenant_id,
                owner_id=owner_id,
                tender_id=tender.id,
                document_id=document_id,
                analysis_type='tender_dashboard',
                result=dashboard,
                summary=summary_block.get('overallAssessment') if isinstance(summary_block, dict) else None,
                score=float((dashboard.get('eligibility') or {}).get('overallScore') or 0),
                confidence=confidence,
                model_used=f"{completion['provider']}:{completion['model']}",
                tokens_used=tokens or None,
            )
            db.add(row)

        doc.processing_status = 'completed'
        doc.processed_at = datetime.now(timezone.utc)
        doc.processing_error = None
        meta = dict(doc.metadata_json or {})
        meta['analysis'] = {
            'status': 'completed',
            'provider': prov,
            'model': mdl,
            'tender_id': tender_id,
            'analysis_id': None,
            'finished_at': datetime.now(timezone.utc).isoformat(),
        }
        doc.metadata_json = meta
        await db.flush()
        meta['analysis']['analysis_id'] = str(row.id)
        doc.metadata_json = meta

        await track_usage(
            db,
            tenant_id=tenant_id,
            user_id=owner_id,
            action='ai_analysis',
            resource_type='analysis',
            resource_id=row.id,
            tokens_used=tokens or None,
            metadata={'provider': prov, 'model': mdl},
        )
        await db.commit()
        await db.refresh(row)

        return {
            'success': True,
            'document_id': str(document_id),
            'tender_id': tender_id,
            'analysis_id': str(row.id),
            'processing_status': 'completed',
            'provider': prov,
            'model': mdl,
        }
    except Exception as exc:
        logger.exception('Document analysis failed for %s', document_id)
        await db.rollback()
        doc = await db.get(Document, document_id)
        if doc:
            doc.processing_status = 'failed'
            doc.processing_error = str(exc)[:2000]
            meta = dict(doc.metadata_json or {})
            meta['analysis'] = {
                'status': 'failed',
                'error': str(exc)[:500],
                'provider': prov,
                'model': mdl,
                'finished_at': datetime.now(timezone.utc).isoformat(),
            }
            doc.metadata_json = meta
            await db.commit()
        raise
