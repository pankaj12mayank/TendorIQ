"""Public (unauthenticated) Lite endpoints — landing CMS content."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.platform.lite_settings import build_public_site

router = APIRouter(prefix='/public', tags=['Public'])


@router.get('/site')
async def public_site(db: AsyncSession = Depends(get_db)):
    """Landing page content and pricing cards (no auth)."""
    data = await build_public_site(db)
    return {'success': True, 'data': data}
