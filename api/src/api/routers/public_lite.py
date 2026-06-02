"""Public (unauthenticated) Lite endpoints — landing CMS content."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Response
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.local_user_auth import PLATFORM_ADMIN_PREF
from ...core.models import AnalysisResult, Document, PlatformSetting, Proposal, Tender, User
from ...core.platform.lite_settings import build_public_site
from ...core.user_preferences import normalize_preferences

router = APIRouter(prefix='/public', tags=['Public'])
PUBLIC_SITE_CACHE_TTL_SECONDS = 5
_PUBLIC_SITE_CACHE: dict[str, object] = {
    'expires_at': datetime.fromtimestamp(0, tz=timezone.utc),
    'stamp': '',
    'payload': None,
}


async def _platform_data_stamp(db: AsyncSession) -> str:
    settings_updated = await db.scalar(select(func.max(PlatformSetting.updated_at)))
    users_updated = await db.scalar(select(func.max(User.updated_at)))
    docs_updated = await db.scalar(select(func.max(Document.updated_at)))
    tenders_updated = await db.scalar(select(func.max(Tender.updated_at)))
    analyses_updated = await db.scalar(select(func.max(AnalysisResult.created_at)))
    proposals_updated = await db.scalar(select(func.max(Proposal.updated_at)))
    parts = [
        settings_updated.isoformat() if settings_updated else '',
        users_updated.isoformat() if users_updated else '',
        docs_updated.isoformat() if docs_updated else '',
        tenders_updated.isoformat() if tenders_updated else '',
        analyses_updated.isoformat() if analyses_updated else '',
        proposals_updated.isoformat() if proposals_updated else '',
    ]
    return '|'.join(parts)


@router.get('/site')
async def public_site(response: Response, db: AsyncSession = Depends(get_db)):
    """Landing page content and pricing cards (no auth)."""
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    now = datetime.now(timezone.utc)
    stamp = await _platform_data_stamp(db)
    cached_payload = _PUBLIC_SITE_CACHE.get('payload')
    cached_stamp = str(_PUBLIC_SITE_CACHE.get('stamp') or '')
    cached_expires_at = _PUBLIC_SITE_CACHE.get('expires_at')
    if (
        cached_payload
        and isinstance(cached_expires_at, datetime)
        and cached_expires_at > now
        and cached_stamp == stamp
    ):
        return {'success': True, 'data': cached_payload}

    data = await build_public_site(db)
    users = (await db.execute(select(User.id, User.preferences))).all()
    companies = 0
    for _, prefs in users:
        if normalize_preferences(prefs).get(PLATFORM_ADMIN_PREF):
            continue
        companies += 1
    tenders_processed = await db.scalar(
        select(func.count(func.distinct(Tender.id))).where(
            Tender.deleted_at.is_(None),
            Tender.status.in_(('published', 'closed', 'awarded')),
            select(AnalysisResult.id)
            .where(AnalysisResult.tender_id == Tender.id)
            .limit(1)
            .exists(),
            select(Proposal.id)
            .where(and_(Proposal.tender_id == Tender.id, Proposal.status != 'deleted'))
            .limit(1)
            .exists(),
        )
    ) or 0
    uploads_total = await db.scalar(
        select(func.count(Document.id)).where(Document.deleted_at.is_(None))
    ) or 0
    completed_jobs = await db.scalar(
        select(func.count(Document.id)).where(
            Document.deleted_at.is_(None),
            Document.processing_status == 'completed',
        )
    ) or 0
    success_rate = round((completed_jobs / uploads_total) * 100, 1) if uploads_total else 0.0
    data['trust_stats'] = {
        'companies': int(companies),
        'tenders_processed': int(tenders_processed),
        'success_rate': success_rate,
        'updated_at': data.get('updated_at'),
    }
    _PUBLIC_SITE_CACHE['stamp'] = stamp
    _PUBLIC_SITE_CACHE['expires_at'] = now + timedelta(seconds=PUBLIC_SITE_CACHE_TTL_SECONDS)
    _PUBLIC_SITE_CACHE['payload'] = data
    return {'success': True, 'data': data}
