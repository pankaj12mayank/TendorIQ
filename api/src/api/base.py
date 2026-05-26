"""API Base Router and Versioning"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from ..core.config import settings

router = APIRouter()


@router.get('/health')
async def health_check() -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={
            'status': 'healthy',
            'environment': settings.NODE_ENV,
            'version': settings.VERSION,
        },
    )


@router.get('/health/ready')
async def readiness_check(request: Request) -> JSONResponse:
    from ..core.database import engine

    db_ok = False
    try:
        async with engine.connect() as conn:
            await conn.execute(text('SELECT 1'))
        db_ok = True
    except Exception:
        pass

    storage_ok = True
    if settings.STORAGE_PROVIDER == 'local':
        try:
            settings.resolved_storage_local_path.mkdir(parents=True, exist_ok=True)
            storage_ok = settings.resolved_storage_local_path.is_dir()
        except OSError:
            storage_ok = False

    ready = db_ok and storage_ok
    status_code = 200 if ready else 503
    return JSONResponse(
        status_code=status_code,
        content={
            'status': 'ready' if ready else 'not ready',
            'checks': {'database': db_ok, 'storage': storage_ok},
            'environment': settings.NODE_ENV,
            'version': settings.VERSION,
        },
    )


@router.get('/')
async def root() -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={
            'name': 'TenderIQ API',
            'version': '1.0.0',
            'docs': '/docs' if settings.is_development else 'API documentation disabled in production',
            'health': '/health',
        },
    )
