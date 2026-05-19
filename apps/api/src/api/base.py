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

    status_code = 200 if db_ok else 503
    return JSONResponse(
        status_code=status_code,
        content={
            'status': 'ready' if db_ok else 'not ready',
            'checks': {'database': db_ok},
            'environment': settings.NODE_ENV,
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
