"""Lite exports — PDF-only, direct download."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.export.lite_policy import lite_formats_payload
from ...core.export.pdf_generator import get_pdf_generator
from ...core.export.report_source import build_tender_report_payload
from ...core.export.schemas import ExportType
from ...core.tenant_utils import parse_tenant_uuid
from ..dependencies.access import TenantUser, require_tenant_member
from ..schemas.base import create_response

router = APIRouter(
    prefix='/exports',
    tags=['Export'],
    dependencies=[Depends(require_tenant_member)],
)


@router.get('/config')
async def export_config(_user: TenantUser):
    """Lite export capabilities (PDF only)."""
    return create_response(lite_formats_payload())


@router.get('/tender/{tender_id}/pdf')
async def download_tender_analysis_pdf(
    tender_id: str,
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
):
    """Stream analysis report PDF (no job queue)."""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Workspace context required')

    from ...core.billing.lite_usage import enforce_quota, track_usage

    tenant_uuid = parse_tenant_uuid(current_user.tenant_id)
    await enforce_quota(db, tenant_uuid, 'export_pdf')

    payload = await build_tender_report_payload(
        db,
        tenant_id=parse_tenant_uuid(current_user.tenant_id),
        tender_id=tender_id,
        user_id=current_user.user_id,
    )
    if not payload.get('sections'):
        raise HTTPException(
            status_code=404,
            detail='No analysis data to export. Complete document analysis first.',
        )

    pdf_bytes = get_pdf_generator().generate_generic_pdf(payload, ExportType.REPORT)
    await track_usage(
        db,
        tenant_id=tenant_uuid,
        user_id=UUID(current_user.user_id),
        action='export',
        resource_type='export',
        metadata={'tender_id': tender_id, 'format': 'pdf'},
    )
    await db.commit()
    safe_name = ''.join(c if c.isalnum() or c in '-_' else '_' for c in payload['title'][:40])
    filename = f"tender-analysis-{safe_name or tender_id[:8]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )
