"""Path classification for auth middleware — TenderIQ Lite."""

AUTH_PUBLIC_PREFIXES = (
    '/api/v1/auth/',
    '/api/v1/public/',
)

TENANT_EXEMPT_PREFIXES = (
    '/health',
    '/health/ready',
    '/docs',
    '/redoc',
    '/openapi.json',
    '/api/v1/auth/',
    '/api/v1/public/',
    '/api/v1/admin/platform',
)

TENANT_SCOPED_PREFIXES = (
    '/api/v1/tenders',
    '/api/v1/documents',
    '/api/v1/files',
    '/api/v1/analysis',
    '/api/v1/ocr',
    '/api/v1/parsing',
    '/api/v1/exports',
    '/api/v1/billing',
    '/api/v1/proposal',
    '/api/v1/admin',
)


def is_auth_public_path(path: str) -> bool:
    if path in ('/',):
        return True
    return any(path.startswith(p) for p in AUTH_PUBLIC_PREFIXES)


def is_tenant_exempt_path(path: str) -> bool:
    return any(path.startswith(p) for p in TENANT_EXEMPT_PREFIXES)


def is_tenant_scoped_path(path: str) -> bool:
    return any(path.startswith(p) for p in TENANT_SCOPED_PREFIXES)
