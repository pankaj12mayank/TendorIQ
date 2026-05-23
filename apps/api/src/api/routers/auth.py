"""Authentication API Router — consolidated (login, me, token refresh, logout, Clerk webhooks)"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from pydantic import BaseModel
from uuid import UUID

from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import get_settings, settings
from ...core.auth import AuthService, AuthContext, ClerkAuthService
from ...core.account_bootstrap import ensure_demo_account, resolve_db_user_session
from ...core.passwords import verify_password
from ..dependencies.audit import audit_logger
from ...core.clerk_bootstrap import ensure_clerk_user, resolve_clerk_tenant_session
from ...core.database import get_db
from ...core.logging import get_logger
from ...core.models import User
from ...core.middleware import get_current_tenant_id
from ...core.local_auth import (
    build_me_response,
    issue_access_token,
    issue_session_tokens,
    login_user_payload as _login_user_payload,
)
from ...core.roles import is_platform_super_admin, normalize_membership_role, PLATFORM_ROLE_SUPER_ADMIN
from ...core.svix_support import SVIX_AVAILABLE, Webhook, WebhookVerificationError
from ..dependencies.auth import get_current_user, CurrentUser

logger = get_logger('auth_api')

router = APIRouter(prefix='/auth', tags=['Authentication'])


def _database_unavailable(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=(
            'Database is unavailable. Ensure MySQL is running, DATABASE_URL in .env is correct, '
            'and run: run.bat (applies migrations automatically).'
        ),
    )


# ── Models ──────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    message: str
    user: Optional[dict] = None
    token: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    token_type: str = 'bearer'


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = 'bearer'


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    role: Optional[str] = None
    tenant_id: Optional[str] = None
    membership_role: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class WebhookPayload(BaseModel):
    type: str
    data: dict


# ── Helpers ─────────────────────────────────────────────────────────

def verify_super_admin_credentials(email: str, password: str) -> bool:
    s = get_settings()
    admin_email = (s.SUPER_ADMIN_EMAIL or '').strip()
    admin_password = (s.SUPER_ADMIN_PASSWORD or '').strip()
    if not admin_email or not admin_password:
        logger.warning("Super Admin credentials not configured in .env")
        return False
    return (
        email.strip().lower() == admin_email.lower()
        and password.strip() == admin_password
    )


def verify_demo_user_credentials(email: str, password: str) -> Optional[dict]:
    s = get_settings()
    demo_email = (s.DEMO_USER_EMAIL or '').strip()
    demo_password = (s.DEMO_USER_PASSWORD or '').strip()
    if not demo_email or not demo_password:
        return None
    if (
        email.strip().lower() == demo_email.lower()
        and password.strip() == demo_password
    ):
        return {
            'email': demo_email,
            'role': (s.DEMO_USER_ROLE or 'admin').strip(),
            'name': (s.DEMO_USER_NAME or 'Demo User').strip(),
        }
    return None


def _login_response(message: str, user: dict, tokens: dict[str, Any]) -> LoginResponse:
    """Login/clerk-session response with access + refresh tokens."""
    return LoginResponse(
        success=True,
        message=message,
        user=user,
        token=tokens['access_token'],
        access_token=tokens['access_token'],
        refresh_token=tokens['refresh_token'],
        expires_in=tokens['expires_in'],
        token_type=tokens['token_type'],
    )


async def _resolve_display_name(
    db: AsyncSession,
    user_id: str,
    email: Optional[str],
    is_super_admin: bool,
) -> Optional[str]:
    if is_super_admin:
        return 'Super Admin'
    try:
        row = await db.get(User, UUID(user_id))
        if row and row.name:
            return row.name
    except (ValueError, TypeError):
        pass
    if email and '@' in email:
        return email.split('@')[0]
    return None


# ── Public endpoints (no auth required) ─────────────────────────────

async def _audit_tenant_login(
    db: AsyncSession,
    tenant_id: str,
    user_id: str,
    email: str,
    http_request: Request,
) -> None:
    try:
        await audit_logger.log_action(
            db,
            UUID(tenant_id),
            UUID(user_id),
            action='login',
            action_type='auth',
            resource_type='session',
            resource_name=email,
            request=http_request,
        )
    except Exception:
        logger.exception('Failed to record login audit event')


@router.post('/login', response_model=LoginResponse)
async def login(
    request: LoginRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Unified email/password login — Super Admin, Demo User (tenant bootstrap), or DB user."""

    if verify_super_admin_credentials(request.email, request.password):
        logger.info("Login successful: super_admin %s", request.email)
        email = request.email.strip().lower()
        tokens = issue_session_tokens(
            user_id='super_admin',
            email=email,
            role=PLATFORM_ROLE_SUPER_ADMIN,
            tenant_id=None,
            membership_role=None,
        )
        return _login_response(
            'Login successful',
            _login_user_payload(
                user_id='super_admin',
                email=email,
                name='Super Admin',
                role=PLATFORM_ROLE_SUPER_ADMIN,
                membership_role=None,
                tenant_id=None,
                is_super_admin=True,
            ),
            tokens,
        )

    demo = verify_demo_user_credentials(request.email, request.password)
    if demo:
        try:
            user_id, tenant_id, membership_role = await ensure_demo_account(
                db,
                email=demo['email'],
                name=demo['name'],
                membership_role=demo['role'],
            )
        except OperationalError as exc:
            logger.exception('Demo account bootstrap failed (database): %s', exc)
            raise _database_unavailable(exc) from exc
        except Exception as exc:
            logger.exception('Demo account bootstrap failed: %s', exc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    'Demo tenant setup failed. Ensure MySQL is running, DATABASE_URL is set, '
                    'and run: alembic upgrade head (or run.bat setup).'
                ),
            ) from exc

        logger.info(
            "Login successful: demo %s role=%s tenant=%s",
            demo['email'],
            membership_role,
            tenant_id,
        )
        tokens = issue_session_tokens(
            user_id=user_id,
            email=demo['email'],
            role=membership_role,
            tenant_id=tenant_id,
            membership_role=membership_role,
        )
        response = _login_response(
            'Login successful',
            _login_user_payload(
                user_id=user_id,
                email=demo['email'],
                name=demo['name'],
                role=membership_role,
                membership_role=membership_role,
                tenant_id=tenant_id,
                is_super_admin=False,
            ),
            tokens,
        )
        await _audit_tenant_login(db, tenant_id, user_id, demo['email'], http_request)
        return response

    try:
        session = await resolve_db_user_session(db, request.email)
    except OperationalError as exc:
        logger.exception('Database unavailable during login: %s', exc)
        raise _database_unavailable(exc) from exc

    if session:
        user_id, email, tenant_id, membership_role = session
        user_row = await db.get(User, UUID(user_id))
        if user_row:
            stored_hash = (user_row.preferences or {}).get('password_hash')
            if stored_hash and not verify_password(request.password, stored_hash):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='Invalid email or password',
                )
        tokens = issue_session_tokens(
            user_id=user_id,
            email=email,
            role=membership_role,
            tenant_id=tenant_id,
            membership_role=membership_role,
        )
        display_name = await _resolve_display_name(db, user_id, email, False)
        response = _login_response(
            'Login successful',
            _login_user_payload(
                user_id=user_id,
                email=email,
                name=display_name,
                role=membership_role,
                membership_role=membership_role,
                tenant_id=tenant_id,
                is_super_admin=False,
            ),
            tokens,
        )
        await _audit_tenant_login(db, tenant_id, user_id, email, http_request)
        return response

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
    )


@router.get('/status')
async def auth_status():
    """Check authentication configuration (no sensitive email in response)."""
    s = get_settings()
    super_admin_configured = bool(
        (s.SUPER_ADMIN_EMAIL or '').strip() and (s.SUPER_ADMIN_PASSWORD or '').strip()
    )
    demo_configured = bool((s.DEMO_USER_EMAIL or '').strip() and (s.DEMO_USER_PASSWORD or '').strip())
    clerk_webhook_secret = bool((s.CLERK_WEBHOOK_SECRET or '').strip())
    return {
        "super_admin_configured": super_admin_configured,
        "demo_user_configured": demo_configured,
        "demo_tenant_slug": (s.DEMO_TENANT_SLUG or 'demo').strip() if demo_configured else None,
        "auth_mode": "local_jwt",
        "super_admin_note": (
            "Platform super_admin uses SUPER_ADMIN_EMAIL/PASSWORD from .env — not a row in users table."
            if super_admin_configured
            else None
        ),
        "clerk_webhook_configured": clerk_webhook_secret,
        "svix_package_available": SVIX_AVAILABLE,
        "tenant_context": {
            "demo_login_includes_tenant_id": demo_configured,
            "super_admin_has_tenant_id": False,
        },
        "message": (
            "Sign in at /sign-in with SUPER_ADMIN_* or DEMO_USER_* from .env"
            if super_admin_configured or demo_configured
            else "Configure SUPER_ADMIN_EMAIL and SUPER_ADMIN_PASSWORD in .env"
        ),
    }


@router.post('/token', response_model=TokenResponse)
async def get_token(user: CurrentUser) -> dict:
    """Get access and refresh tokens for authenticated user (via Clerk/SSO)."""
    membership_role = user.membership_role or normalize_membership_role(user.role)
    return issue_session_tokens(
        user_id=user.user_id,
        email=user.email or '',
        role=user.role or membership_role,
        tenant_id=user.tenant_id,
        membership_role=membership_role,
    )


@router.post('/refresh', response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest) -> dict:
    """Refresh access token using refresh token."""
    payload = AuthService().verify_token(request.refresh_token)
    if not payload or payload.exp < datetime.now(timezone.utc).timestamp():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid or expired refresh token',
        )
    membership_role = payload.membership_role or normalize_membership_role(payload.role)
    tokens = issue_session_tokens(
        user_id=payload.sub,
        email=payload.email or '',
        role=payload.role or membership_role,
        tenant_id=payload.tenant_id,
        membership_role=membership_role,
    )
    return {
        'access_token': tokens['access_token'],
        'refresh_token': request.refresh_token,
        'expires_in': tokens['expires_in'],
        'token_type': 'bearer',
    }


@router.post('/clerk/session', response_model=LoginResponse)
async def clerk_session_exchange(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """Exchange a Clerk session JWT for a TenderIQ local JWT (tenant-aware when membership exists)."""
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Missing Clerk bearer token',
        )
    token = authorization.replace('Bearer ', '').strip()
    clerk_user = await ClerkAuthService.verify_token(token)
    if not clerk_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid Clerk session',
        )
    try:
        user = await ensure_clerk_user(db, clerk_user)
        user_id, tenant_id, membership_role = await resolve_clerk_tenant_session(db, user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    email = user.email
    tokens = issue_session_tokens(
        user_id=user_id,
        email=email,
        role=membership_role,
        tenant_id=tenant_id,
        membership_role=membership_role,
    )
    return _login_response(
        'Clerk session exchanged',
        _login_user_payload(
            user_id=user_id,
            email=email,
            name=user.name,
            role=membership_role,
            membership_role=membership_role,
            tenant_id=tenant_id,
            is_super_admin=False,
        ),
        tokens,
    )


# ── Protected endpoints (auth required) ─────────────────────────────

@router.get('/me')
async def get_current_user_info(
    request: Request,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get current user information (stable contract for web session restore)."""
    s = get_settings()
    is_super_admin = current_user.is_super_admin() or (
        current_user.email
        and current_user.email.lower() == (s.SUPER_ADMIN_EMAIL or '').strip().lower()
    )
    tenant_id = get_current_tenant_id(request) or current_user.tenant_id
    name = await _resolve_display_name(
        db,
        current_user.user_id,
        current_user.email,
        is_super_admin,
    )
    return build_me_response(
        current_user,
        name=name,
        tenant_id=tenant_id,
        is_super_admin=is_super_admin,
    )


@router.post('/logout')
async def logout(
    current_user: CurrentUser,
    authorization: Optional[str] = Header(None),
) -> dict:
    """Logout user and revoke the current access token jti."""
    auth_service = AuthService()
    if authorization and authorization.startswith('Bearer '):
        token = authorization.replace('Bearer ', '').strip()
        payload = auth_service.verify_token(token)
        if payload:
            auth_service.revoke_token(payload.jti)
    logger.info('User logged out', user_id=current_user.user_id)
    return {'message': 'Logged out successfully'}


@router.post('/clerk/webhook')
async def clerk_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Handle Clerk webhooks (Svix) and bootstrap DB users."""
    secret = (settings.CLERK_WEBHOOK_SECRET or '').strip()
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Clerk webhooks are not configured',
        )
    if not SVIX_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Clerk webhooks require the svix package (pip install -r requirements-dev.txt)',
        )

    body = await request.body()
    wh = Webhook(secret)
    try:
        wh.verify(
            body,
            {
                'svix-id': request.headers.get('svix-id') or '',
                'svix-timestamp': request.headers.get('svix-timestamp') or '',
                'svix-signature': request.headers.get('svix-signature') or '',
            },
        )
    except WebhookVerificationError:
        logger.warning('Invalid Clerk webhook signature')
        raise HTTPException(status_code=400, detail='Invalid webhook signature')

    try:
        event = json.loads(body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail='Invalid JSON payload') from exc

    event_type = event.get('type', '')
    data = event.get('data', {})
    logger.info('Clerk webhook received', type=event_type)
    if event_type == 'user.created':
        try:
            await ensure_clerk_user(db, data)
        except ValueError as exc:
            logger.warning('Clerk user.created bootstrap skipped: %s', exc)
    elif event_type == 'user.updated':
        try:
            await ensure_clerk_user(db, data)
        except ValueError as exc:
            logger.warning('Clerk user.updated bootstrap skipped: %s', exc)
    elif event_type == 'user.deleted':
        logger.info('User deleted via Clerk', user_id=data.get('id'))
    return {'status': 'received'}
