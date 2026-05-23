"""Virus scan gate for uploads — invoked from document/file routes."""

from __future__ import annotations

from fastapi import HTTPException, status

from .virus_scan import virus_scanner


async def assert_upload_clean(file_content: bytes, filename: str) -> dict:
    """Scan bytes before persisting; raises 400 when infected."""
    result = await virus_scanner.scan_file(file_content, filename or 'upload')
    if result.get('infected'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get('message', 'File failed virus scan'),
        )
    return result
