"""Parsing API Router"""

import re
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, delete, update

from ..dependencies.auth import CurrentUser
from ..services.document_service import document_service
from ...core.parsers import parser_service, ChunkingStrategy
from ...core.storage import storage_service
from ...core.logging import get_logger
from ...core.models import ParsedDocument as ParsedDocumentModel
from ...core.models import DocumentChunk as DocumentChunkModel

router = APIRouter(prefix='/parsing', tags=['parsing'])
logger = get_logger('parsing_api')


@router.post('/document/{document_id}')
async def parse_document(
    document_id: str,
    current_user: CurrentUser,
    db=None,
    chunk: bool = Query(True),
    strategy: str = Query('hybrid'),
):
    """Parse a document and optionally create chunks"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    doc = await document_service.get_document(
        db, UUID(document_id), UUID(current_user.tenant_id)
    )
    if not doc:
        raise HTTPException(status_code=404, detail='Document not found')

    if doc.processing_status == 'processing':
        raise HTTPException(status_code=400, detail='Document is being processed')

    try:
        signed_result = storage_service.generate_signed_download_url(
            storage_key=doc.storage_key,
            expires_seconds=3600,
        )

        if not signed_result.get('success'):
            raise HTTPException(status_code=500, detail='Failed to get file')

        import httpx
        response = httpx.get(signed_result['download_url'], timeout=120.0)
        response.raise_for_status()
        file_bytes = response.content

        parsed_doc, chunking_result = await parser_service.parse(
            file_bytes=file_bytes,
            file_name=doc.file_name,
            document_id=document_id,
            chunk=chunk,
            chunking_strategy=strategy,
        )

        parsed_record = ParsedDocumentModel(
            document_id=UUID(document_id),
            tenant_id=UUID(current_user.tenant_id),
            file_name=doc.file_name,
            file_type=doc.file_type,
            metadata_json={
                'title': parsed_doc.metadata.title,
                'author': parsed_doc.metadata.author,
                'keywords': parsed_doc.metadata.keywords,
                'page_count': parsed_doc.metadata.page_count,
                'word_count': parsed_doc.metadata.word_count,
            },
            full_text=parsed_doc.full_text,
            page_count=parsed_doc.metadata.page_count or len(parsed_doc.pages),
            word_count=len(parsed_doc.full_text.split()),
            confidence_score=parsed_doc.confidence_score,
            sections_json=[{'title': s.title, 'level': s.level, 'content': s.content, 'word_count': s.word_count} for s in parsed_doc.sections],
            tables_json=parsed_doc.tables,
            links_json=parsed_doc.links,
            status='completed',
            chunk_count=chunking_result.chunk_count if chunking_result else 0,
            chunking_strategy=strategy,
            completed_at=datetime.now(timezone.utc),
        )
        db.add(parsed_record)
        await db.flush()

        if chunking_result:
            for ch in chunking_result.chunks:
                chunk_record = DocumentChunkModel(
                    document_id=UUID(document_id),
                    parsed_document_id=parsed_record.id,
                    tenant_id=UUID(current_user.tenant_id),
                    chunk_index=ch.chunk_index,
                    content=ch.text,
                    start_char=ch.start_char,
                    end_char=ch.end_char,
                    start_page=ch.start_page,
                    end_page=ch.end_page,
                    section_path=ch.section_path,
                    tokens=ch.tokens,
                    metadata=ch.metadata_json or {},
                )
                db.add(chunk_record)

        await db.commit()

        await document_service.update_document(
            db, UUID(document_id), UUID(current_user.tenant_id),
            processing_status='completed',
            metadata={**(doc.metadata_json or {}), 'parsed': True},
        )

        return {
            'success': True,
            'document_id': document_id,
            'parsed_document_id': str(parsed_record.id),
            'word_count': len(parsed_doc.full_text.split()),
            'page_count': parsed_doc.metadata.page_count or len(parsed_doc.pages),
            'chunk_count': chunking_result.chunk_count if chunking_result else 0,
            'confidence_score': parsed_doc.confidence_score,
            'sections_found': len(parsed_doc.sections),
        }

    except Exception as e:
        logger.error(f'Parsing failed for document {document_id}: {e}')
        await document_service.update_document(
            db, UUID(document_id), UUID(current_user.tenant_id),
            processing_status='failed',
        )
        raise HTTPException(status_code=500, detail=f'Parsing failed: {str(e)}')


@router.get('/status/{document_id}')
async def get_parsing_status(
    document_id: str,
    current_user: CurrentUser,
    db=None,
):
    """Get document parsing status"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    result = await db.execute(
        select(ParsedDocumentModel)
        .where(
            ParsedDocumentModel.document_id == UUID(document_id),
            ParsedDocumentModel.tenant_id == UUID(current_user.tenant_id),
        )
        .order_by(ParsedDocumentModel.created_at.desc())
    )
    parsed = result.scalar_one_or_none()

    doc = await document_service.get_document(
        db, UUID(document_id), UUID(current_user.tenant_id)
    )

    if not doc:
        raise HTTPException(status_code=404, detail='Document not found')

    chunk_count = parsed.chunk_count if parsed else 0

    return {
        'success': True,
        'document_id': document_id,
        'status': doc.processing_status,
        'has_parsed': parsed is not None,
        'has_chunks': chunk_count > 0,
        'word_count': parsed.word_count if parsed else 0,
        'chunk_count': chunk_count,
        'confidence_score': parsed.confidence_score if parsed else 0.0,
    }


@router.get('/result/{document_id}')
async def get_parsed_result(
    document_id: str,
    current_user: CurrentUser,
    db=None,
    include_chunks: bool = Query(False),
):
    """Get parsed document result"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    result = await db.execute(
        select(ParsedDocumentModel)
        .where(
            ParsedDocumentModel.document_id == UUID(document_id),
            ParsedDocumentModel.tenant_id == UUID(current_user.tenant_id),
        )
        .order_by(ParsedDocumentModel.created_at.desc())
    )
    parsed = result.scalar_one_or_none()

    if not parsed:
        raise HTTPException(status_code=404, detail='Parsing result not found')

    response = {
        'success': True,
        'document_id': document_id,
        'file_name': parsed.file_name,
        'file_type': parsed.file_type,
        'metadata': parsed.metadata_json,
        'full_text': parsed.full_text,
        'word_count': parsed.word_count,
        'page_count': parsed.page_count,
        'confidence_score': parsed.confidence_score,
        'sections': parsed.sections_json,
        'tables': parsed.tables_json,
        'links': parsed.links_json,
        'status': parsed.status,
    }

    if include_chunks:
        chunks_result = await db.execute(
            select(DocumentChunkModel)
            .where(DocumentChunkModel.document_id == UUID(document_id))
            .order_by(DocumentChunkModel.chunk_index)
        )
        chunks = chunks_result.scalars().all()
        response['chunks'] = [
            {
                'id': str(c.id),
                'chunk_index': c.chunk_index,
                'text': c.content,
                'start_char': c.start_char,
                'end_char': c.end_char,
                'start_page': c.start_page,
                'end_page': c.end_page,
                'section_path': c.section_path,
                'tokens': c.tokens,
            }
            for c in chunks
        ]

    return response


@router.get('/preview/{document_id}')
async def preview_parsing(
    document_id: str,
    current_user: CurrentUser,
    db=None,
    max_chars: int = Query(5000, ge=100, le=50000),
):
    """Preview parsed text"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    result = await db.execute(
        select(ParsedDocumentModel)
        .where(
            ParsedDocumentModel.document_id == UUID(document_id),
            ParsedDocumentModel.tenant_id == UUID(current_user.tenant_id),
        )
        .order_by(ParsedDocumentModel.created_at.desc())
    )
    parsed = result.scalar_one_or_none()

    if not parsed or not parsed.full_text:
        raise HTTPException(status_code=404, detail='No parsed content found')

    preview = parsed.full_text[:max_chars]
    if len(parsed.full_text) > max_chars:
        preview += '... [truncated]'

    return {
        'success': True,
        'preview_text': preview,
        'word_count': parsed.word_count,
        'total_chars': len(parsed.full_text),
        'confidence_score': parsed.confidence_score,
    }


@router.delete('/result/{document_id}')
async def delete_parsing_result(
    document_id: str,
    current_user: CurrentUser,
    db=None,
):
    """Delete parsing result and chunks"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    result = await db.execute(
        select(ParsedDocumentModel)
        .where(
            ParsedDocumentModel.document_id == UUID(document_id),
            ParsedDocumentModel.tenant_id == UUID(current_user.tenant_id),
        )
    )
    parsed = result.scalar_one_or_none()

    if not parsed:
        raise HTTPException(status_code=404, detail='Parsing result not found')

    await db.execute(
        delete(DocumentChunkModel).where(
            DocumentChunkModel.document_id == UUID(document_id)
        )
    )
    await db.execute(
        delete(ParsedDocumentModel).where(
            ParsedDocumentModel.id == parsed.id
        )
    )

    await db.commit()

    return {'success': True, 'document_id': document_id}