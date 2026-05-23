"""Path classification for tenant middleware."""

# No bearer / tenant enforcement (public or auth bootstrap)
AUTH_PUBLIC_PREFIXES = (
    '/api/v1/auth/',
    '/api/v1/webhooks/',
    '/api/v1/sso/session',
    '/api/v1/sso/public/',
)

TENANT_EXEMPT_PREFIXES = (
    '/health',
    '/health/ready',
    '/docs',
    '/redoc',
    '/openapi.json',
    '/api/v1/auth/',
    '/api/v1/webhooks/',
    '/api/v1/admin/platform',
    '/api/v1/onboarding',
    '/api/v1/observability/health',
    '/api/v1/sso/session',
    '/api/v1/sso/public/',
)

# Routes that need tenant_id on request.state when user is authenticated
TENANT_SCOPED_PREFIXES = (
    '/api/v1/tenders',
    '/api/v1/documents',
    '/api/v1/files',
    '/api/v1/analysis',
    '/api/v1/ocr',
    '/api/v1/parsing',
    '/api/v1/bids',
    '/api/v1/review',
    '/api/v1/export',
    '/api/v1/notifications',
    '/api/v1/billing',
    '/api/v1/organizations',
    '/api/v1/ai',
    '/api/v1/orchestrator',
    '/api/v1/extraction',
    '/api/v1/risk',
    '/api/v1/checklist',
    '/api/v1/proposal',
    '/api/v1/audit',
    '/api/v1/observability',
    '/api/v1/email',
    '/api/v1/queue',
)


def is_auth_public_path(path: str) -> bool:
    if path in ('/',):
        return True
    return any(path.startswith(p) for p in AUTH_PUBLIC_PREFIXES)


def is_tenant_exempt_path(path: str) -> bool:
    return any(path.startswith(p) for p in TENANT_EXEMPT_PREFIXES)


def is_tenant_scoped_path(path: str) -> bool:
    return any(path.startswith(p) for p in TENANT_SCOPED_PREFIXES)
