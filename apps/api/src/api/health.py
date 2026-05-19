"""Health check endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.database import get_db

router = APIRouter(prefix='/health', tags=['Health'])


@router.get('')
async def liveness():
    return {'status': 'alive', 'environment': settings.NODE_ENV}


@router.get('/ready')
async def readiness(db: AsyncSession = Depends(get_db)):
    db_ok = False
    try:
        await db.execute(text('SELECT 1'))
        db_ok = True
    except Exception:
        pass

    return {
        'status': 'ready' if db_ok else 'not ready',
        'database': 'connected' if db_ok else 'disconnected',
        'environment': settings.NODE_ENV,
    }
