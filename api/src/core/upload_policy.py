"""TenderIQ Lite upload policy (Phase 3 — PDF/DOCX, 25MB)."""

from __future__ import annotations

LITE_MAX_FILE_SIZE_MB = 25
LITE_ALLOWED_EXTENSIONS = ('.pdf', '.doc', '.docx')
LITE_ALLOWED_EXTENSIONS_CSV = ','.join(LITE_ALLOWED_EXTENSIONS)

LITE_MIME_BY_EXT: dict[str, str] = {
    '.pdf': 'application/pdf',
    '.doc': 'application/msword',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
}


def lite_extensions_list() -> list[str]:
    return list(LITE_ALLOWED_EXTENSIONS)
