"""TenderIQ Lite API — minimal MVP surface."""

import logging
import os

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from .api.schemas.base import create_error_response

from .core.config import settings
from .core.database import init_db, close_db
from .core.logging import configure_logging, get_logger
from .core.middleware import (
    AuthMiddleware,
    RequestIDMiddleware,
    TimingMiddleware,
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
)
from .api.base import router as base_router
from .api.routers.tenders import router as tenders_router
from .api.routers.auth import router as auth_router
from .api.routers.files import public_storage_router, router as files_router
from .api.routers.documents import router as documents_router
from .api.routers.ocr import router as ocr_router
from .api.routers.parsing import router as parsing_router
from .api.router.analysis import router as analysis_router
from .api.routers.ai_processing import router as ai_processing_router
from .api.routers.lite_proposals import router as lite_proposals_router
from .api.routers.lite_exports import router as lite_exports_router
from .api.routers.payments_lite import router as payments_lite_router
from .api.router.billing import router as billing_router
from .api.router.admin_auth import router as admin_auth_router
from .api.router.admin_platform import router as admin_platform_router
from .api.router.admin_dashboard import router as admin_dashboard_router
from .api.routers.public_lite import router as public_lite_router

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('Starting TenderIQ Lite API in %s mode', settings.NODE_ENV)

    try:
        from .core.observability.sentry import init_sentry

        init_sentry()
    except Exception as exc:
        logger.warning('Sentry init skipped: %s', exc)

    await init_db()

    from .core.storage.paths import ensure_local_storage_root

    root = ensure_local_storage_root()
    if settings.STORAGE_PROVIDER == 'local':
        logger.info('Local storage root: %s', root)

    try:
        from .core.processing.tasks import recover_stuck_documents

        recovered = await recover_stuck_documents()
        if recovered:
            logger.info('Recovered %d stuck document(s) on startup', recovered)
    except Exception as exc:
        logger.warning('Document recovery skipped: %s', exc)

    yield

    await close_db()
    logger.info('Database closed')
    logger.info('TenderIQ Lite API shutdown complete')


app = FastAPI(
    title=settings.APP_NAME,
    description='TenderIQ Lite — tender analysis MVP API',
    version=settings.VERSION,
    docs_url='/docs' if not settings.is_production else None,
    redoc_url='/redoc' if not settings.is_production else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.cors_allow_methods_list,
    allow_headers=settings.cors_allow_headers_list,
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(TimingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(AuthMiddleware)


@app.middleware('http')
async def log_requests(request: Request, call_next):
    request_id = getattr(request.state, 'request_id', 'unknown')
    log = get_logger(__name__).bind(request_id=request_id)
    log.info('Request', method=request.method, path=request.url.path)
    response = await call_next(request)
    log.info('Response', status_code=response.status_code)
    return response


@app.middleware('http')
async def no_store_api_cache(request: Request, call_next):
    response = await call_next(request)
    path = request.url.path
    no_store_prefixes = (
        '/api/v1/auth',
        '/api/v1/files',
        '/api/v1/documents',
        '/api/v1/tenders',
        '/api/v1/analysis',
        '/api/v1/proposals',
        '/api/v1/billing',
        '/api/v1/payments',
        '/api/v1/admin/platform/dashboard',
        '/api/v1/admin/platform/analytics',
    )
    if path.startswith(no_store_prefixes):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response


def _http_exception_message(detail: object) -> str:
    if isinstance(detail, str):
        return detail
    if isinstance(detail, dict):
        msg = detail.get('message')
        if msg:
            return str(msg)
    if isinstance(detail, list):
        parts: list[str] = []
        for item in detail:
            if isinstance(item, dict):
                loc = '.'.join(str(x) for x in item.get('loc', ()))
                parts.append(f'{loc}: {item.get("msg", "")}'.strip(': '))
            else:
                parts.append(str(item))
        return '; '.join(parts) or 'Request failed'
    return str(detail)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    message = _http_exception_message(exc.detail)
    details = None if isinstance(exc.detail, str) else {'detail': exc.detail}
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(f'HTTP_{exc.status_code}', message, details),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Request validation failed',
                'details': exc.errors(),
            },
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, 'request_id', 'unknown')
    log = get_logger(__name__).bind(request_id=request_id)
    log.error('Unhandled exception: %s', exc, exc_info=True)
    error_payload: dict = {
        'code': 'INTERNAL_ERROR',
        'message': 'An unexpected error occurred',
        'request_id': request_id,
    }
    if settings.expose_error_details:
        error_payload['detail'] = str(exc)
    return JSONResponse(status_code=500, content={'success': False, 'error': error_payload})


app.include_router(base_router, tags=['Base'])
app.include_router(admin_platform_router, prefix='/api/v1')
app.include_router(admin_dashboard_router, prefix='/api/v1')
app.include_router(public_lite_router, prefix='/api/v1')
app.include_router(auth_router, prefix='/api/v1')
app.include_router(tenders_router, prefix='/api/v1')
app.include_router(public_storage_router, prefix='/api/v1')
app.include_router(files_router, prefix='/api/v1')
app.include_router(documents_router, prefix='/api/v1')
app.include_router(ocr_router, prefix='/api/v1')
app.include_router(parsing_router, prefix='/api/v1')
app.include_router(analysis_router, prefix='/api/v1')
app.include_router(ai_processing_router, prefix='/api/v1')
app.include_router(lite_proposals_router, prefix='/api/v1')
app.include_router(lite_exports_router, prefix='/api/v1')
app.include_router(billing_router, prefix='/api/v1')
app.include_router(payments_lite_router, prefix='/api/v1')
app.include_router(admin_auth_router, prefix='/api/v1')


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(
        'src.main:app',
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        workers=settings.WORKERS if not settings.RELOAD else 1,
    )
