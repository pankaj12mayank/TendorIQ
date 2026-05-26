"""TenderIQ Lite — PDF-only export policy (Phase 6)."""

from __future__ import annotations

from fastapi import HTTPException

from ..config import settings
from .schemas import ExportFormat

LITE_EXPORT_FORMATS = (ExportFormat.PDF,)


def lite_export_pdf_only() -> bool:
    return bool(getattr(settings, 'LITE_EXPORT_PDF_ONLY', True))


def assert_lite_export_format(fmt: ExportFormat) -> None:
    if lite_export_pdf_only() and fmt != ExportFormat.PDF:
        raise HTTPException(
            status_code=400,
            detail='TenderIQ Lite supports PDF export only. Set format=pdf or use GET /exports/tender/{id}/pdf',
        )


def lite_formats_payload() -> dict:
    return {
        'pdf_only': lite_export_pdf_only(),
        'formats': [
            {
                'id': 'pdf',
                'name': 'PDF',
                'description': 'Print-ready PDF with your company header',
                'extension': '.pdf',
                'mime_type': 'application/pdf',
            }
        ],
    }
