"""Health Check and Readiness Endpoints"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from tendoriq.shared import env

from ..core.database import get_db
from ..core.redis import get_redis

router = APIRouter(prefix='/health', tags=['Health'])


@router.get('')
async def liveness():
    return {'status': 'alive', 'environment': env.NODE_ENV}


@router.get('/ready')
async def readiness(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute('SELECT 1')
        redis_ok = True
    except Exception:
        redis_ok = False

    return {
        'status': 'ready' if redis_ok else 'not ready',
        'database': 'connected',
        'redis': 'connected' if redis_ok else 'disconnected',
        'environment': env.NODE_ENV,
    }