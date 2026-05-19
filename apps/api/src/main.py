"""TenderIQ API - Main Application Entry Point"""

import logging

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from .core.config import settings
from .core.database import init_db, close_db
from .core.logging import configure_logging, get_logger
from .core.middleware import (
    RequestIDMiddleware,
    TimingMiddleware,
    SecurityHeadersMiddleware,
)
from .core.tenant_middleware import TenantMiddleware
from .api.base import router as base_router
from .api.routers.tenders import router as tenders_router
from .api.routers.organizations import router as organizations_router
from .api.routers.auth import router as auth_router
from .api.tenants import router as tenants_router
from .api.routers.onboarding import router as onboarding_router
from .api.routers.files import router as files_router
from .api.routers.documents import router as documents_router
from .api.routers.ocr import router as ocr_router
from .api.routers.parsing import router as parsing_router
from .api.router.queue import router as queue_router
from .api.router.ai import router as ai_router
from .api.router.orchestrator import router as orchestrator_router
from .api.router.prompt_mgmt import router as prompt_mgmt_router
from .api.router.extraction import router as extraction_router
from .api.router.risk import router as risk_router
from .api.router.checklist import router as checklist_router
from .api.router.proposal import router as proposal_router
from .api.router.export import router as export_router
from .api.router.review import router as review_router
from .api.router.email import router as email_router
from .api.router.audit import router as audit_router
from .api.router.observability import router as observability_router
from .api.router.billing import router as billing_router
from .api.router.sso import router as sso_router
from .api.router.admin_auth import router as admin_auth_router
from .api.router.super_admin import router as super_admin_router
from .api.router.email_system import router as email_system_router

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f'Starting TenderIQ API in {settings.NODE_ENV} mode')

    await init_db()

    try:
        from .core.database import async_session_maker
        from .core.email.seed import seed_email_system

        async with async_session_maker() as db:
            await seed_email_system(db)
    except Exception as exc:
        logger.warning('Email system seed skipped: %s', exc)

    yield

    await close_db()
    logger.info('Database closed')

    logger.info('TenderIQ API shutdown complete')


app = FastAPI(
    title=settings.APP_NAME,
    description='TenderIQ - Tender Management Platform API',
    version=settings.VERSION,
    docs_url='/docs' if not settings.is_production else None,
    redoc_url='/redoc' if not settings.is_production else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(TimingMiddleware)
app.add_middleware(TenantMiddleware)
app.add_middleware(RequestIDMiddleware)


@app.middleware('http')
async def log_requests(request: Request, call_next):
    request_id = getattr(request.state, 'request_id', 'unknown')
    logger = get_logger(__name__).bind(request_id=request_id)

    logger.info(
        'Request',
        method=request.method,
        path=request.url.path,
        client=request.client.host if request.client else 'unknown',
    )

    response = await call_next(request)

    logger.info(
        'Response',
        status_code=response.status_code,
    )

    return response


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
    logger = get_logger(__name__).bind(request_id=request_id)
    logger.error(f'Unhandled exception: {exc}', exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred',
            },
        },
    )


app.include_router(base_router, tags=['Base'])
app.include_router(auth_router, prefix='/api/v1')
app.include_router(tenders_router, prefix='/api/v1')
app.include_router(organizations_router, prefix='/api/v1')
app.include_router(tenants_router, prefix='/api/v1')
app.include_router(onboarding_router, prefix='/api/v1')
app.include_router(files_router, prefix='/api/v1')
app.include_router(documents_router, prefix='/api/v1')
app.include_router(ocr_router, prefix='/api/v1')
app.include_router(parsing_router, prefix='/api/v1')
app.include_router(queue_router, prefix='/api/v1')
app.include_router(ai_router, prefix='/api/v1')
app.include_router(orchestrator_router, prefix='/api/v1')
app.include_router(prompt_mgmt_router, prefix='/api/v1')
app.include_router(extraction_router, prefix='/api/v1')
app.include_router(risk_router, prefix='/api/v1')
app.include_router(checklist_router, prefix='/api/v1')
app.include_router(proposal_router, prefix='/api/v1')
app.include_router(export_router, prefix='/api/v1')
app.include_router(review_router, prefix='/api/v1')
app.include_router(email_router, prefix='/api/v1')
app.include_router(audit_router, prefix='/api/v1')
app.include_router(observability_router, prefix='/api/v1')
app.include_router(billing_router, prefix='/api/v1')
app.include_router(sso_router, prefix='/api/v1')
app.include_router(admin_auth_router, prefix='/api/v1')
app.include_router(super_admin_router, prefix='/api/v1')
app.include_router(email_system_router, prefix='/api/v1')


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(
        'main:app',
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        workers=settings.WORKERS if not settings.RELOAD else 1,
    )