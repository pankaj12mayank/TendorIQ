"""API Base Router and Versioning"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from tendoriq.shared import env, isDev

router = APIRouter()


@router.get('/health')
async def health_check() -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={
            'status': 'healthy',
            'environment': env.NODE_ENV,
            'version': '1.0.0',
        },
    )


@router.get('/health/ready')
async def readiness_check(request: Request) -> JSONResponse:
    from ..core.database import engine
    from ..core.redis import get_redis

    checks = {'database': False, 'redis': False}

    try:
        async with engine.connect() as conn:
            await conn.execute('SELECT 1')
        checks['database'] = True
    except Exception:
        pass

    try:
        redis = get_redis()
        await redis.ping()
        checks['redis'] = True
    except Exception:
        pass

    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503

    return JSONResponse(
        status_code=status_code,
        content={
            'status': 'ready' if all_healthy else 'not ready',
            'checks': checks,
            'environment': env.NODE_ENV,
        },
    )


@router.get('/')
async def root() -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={
            'name': 'TenderIQ API',
            'version': '1.0.0',
            'docs': '/docs' if isDev else 'API documentation disabled in production',
            'health': '/health',
        },
    )