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
from ...core.local_user_auth import (
    PLATFORM_ADMIN_PREF,
    authenticate_email_password,
    change_user_password,
    owner_account_file_path,
    register_email_password,
    seed_initial_accounts_if_empty,
)
from ...core.clerk_bootstrap import ensure_clerk_user, resolve_clerk_tenant_session
from ...core.supabase_auth import verify_supabase_access_token
from ...core.supabase_bootstrap import ensure_supabase_user, resolve_supabase_session
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
from ..dependencies.access import LiteUser
from ...core.personal_workspace import (
    ensure_personal_workspace,
    get_company_profile_dict,
)
from ...core.models import CompanyProfile

logger = get_logger('auth_api')

router = APIRouter(prefix='/auth', tags=['Authentication'])


def _database_unavailable(exc: Exception) -> HTTPException:
    msg = str(exc).lower()
    if 'no such column' in msg or 'no such table' in msg:
        detail = (
            'Database schema is out of date. Stop servers, then run: run.bat setup '
            '(or: cd api && venv\\Scripts\\python.exe -m alembic upgrade head).'
        )
    else:
        detail = (
            'Database is unavailable. Check DATABASE_URL in .env and run: run.bat '
            '(applies migrations automatically).'
        )
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=detail,
    )


# ── Models ──────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


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
    try:
        row = await db.get(User, UUID(user_id))
        if row and row.name:
            return row.name
        if row and is_super_admin:
            return row.name or 'Platform Admin'
    except (ValueError, TypeError):
        pass
    if email and '@' in email:
        return email.split('@')[0]
    return None


# ── Public endpoints (no auth required) ─────────────────────────────

@router.post('/login', response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Email/password login — credentials must exist in the database."""
    try:
        result = await authenticate_email_password(db, request.email, request.password)
    except OperationalError as exc:
        logger.exception('Database unavailable during login: %s', exc)
        raise _database_unavailable(exc) from exc

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid email or password',
        )

    user_payload, tokens = result
    logger.info('Login successful: %s', user_payload.get('email'))
    return _login_response('Login successful', user_payload, tokens)


@router.post('/register', response_model=LoginResponse)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a database user and sign in (local auth)."""
    try:
        user_payload, tokens = await register_email_password(
            db,
            email=request.email,
            password=request.password,
            name=request.name,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except OperationalError as exc:
        logger.exception('Database unavailable during register: %s', exc)
        raise _database_unavailable(exc) from exc

    return _login_response('Account created', user_payload, tokens)


@router.post('/bootstrap-seed', include_in_schema=False)
async def bootstrap_seed(db: AsyncSession = Depends(get_db)):
    """Dev/first-run: seed accounts when no password users exist (idempotent)."""
    if settings.NODE_ENV == 'production':
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Not found')
    try:
        created = await seed_initial_accounts_if_empty(db)
    except OperationalError as exc:
        raise _database_unavailable(exc) from exc
    return {
        'created': created,
        'message': (
            'Bootstrap accounts created. See .tenderiq/bootstrap-credentials.json'
            if created
            else 'Users already exist; seed skipped'
        ),
    }


@router.get('/status')
async def auth_status(db: AsyncSession = Depends(get_db)):
    """Check authentication configuration (no secrets in response)."""
    from ...core.local_user_auth import count_password_users

    try:
        password_users = await count_password_users(db)
    except OperationalError:
        password_users = 0
    clerk_webhook_secret = bool((settings.CLERK_WEBHOOK_SECRET or '').strip())
    return {
        'auth_mode': (settings.AUTH_PROVIDER or 'local').strip().lower(),
        'password_users': password_users,
        'registration_available': settings.AUTH_PROVIDER == 'local',
        'clerk_webhook_configured': clerk_webhook_secret,
        'svix_package_available': SVIX_AVAILABLE,
        'message': 'Sign in with your account email and password',
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


@router.post('/supabase/session', response_model=LoginResponse)
async def supabase_session_exchange(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """Exchange a Supabase access token for TenderIQ API JWT + user profile."""
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Missing Supabase bearer token',
        )
    token = authorization.replace('Bearer ', '').strip()
    claims = verify_supabase_access_token(token)
    if not claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid Supabase session',
        )
    try:
        user = await ensure_supabase_user(db, claims)
        user_id, tenant_id, membership_role = await resolve_supabase_session(db, user)
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
        'Supabase session exchanged',
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
    current_user: LiteUser,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get current user information (stable contract for web session restore)."""
    is_super_admin = current_user.is_super_admin()
    if not is_super_admin and current_user.user_id:
        try:
            row = await db.get(User, UUID(current_user.user_id))
            if row and isinstance(row.preferences, dict):
                is_super_admin = bool(row.preferences.get(PLATFORM_ADMIN_PREF))
        except (ValueError, TypeError):
            pass
    tenant_id = get_current_tenant_id(request) or current_user.tenant_id
    name = await _resolve_display_name(
        db,
        current_user.user_id,
        current_user.email,
        is_super_admin,
    )
    company_profile = None
    if not is_super_admin:
        company_profile = await get_company_profile_dict(db, current_user.user_id)
    return build_me_response(
        current_user,
        name=name,
        tenant_id=tenant_id,
        is_super_admin=is_super_admin,
        company_profile=company_profile,
    )


class CompanyProfileUpdate(BaseModel):
    company_name: Optional[str] = None
    industry: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    tax_id: Optional[str] = None
    logo_url: Optional[str] = None


class AiPreferencesUpdate(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    style: Optional[str] = None
    tone: Optional[str] = None


@router.get('/me/company-profile')
async def get_company_profile(
    current_user: LiteUser,
    db: AsyncSession = Depends(get_db),
) -> dict:
    profile = await get_company_profile_dict(db, current_user.user_id)
    if not profile:
        await ensure_personal_workspace(db, current_user.user_id, current_user.email)
        profile = await get_company_profile_dict(db, current_user.user_id)
    return profile or {}


@router.patch('/me/company-profile')
async def update_company_profile(
    body: CompanyProfileUpdate,
    current_user: LiteUser,
    db: AsyncSession = Depends(get_db),
) -> dict:
    await ensure_personal_workspace(db, current_user.user_id, current_user.email)
    from sqlalchemy import select

    result = await db.execute(
        select(CompanyProfile).where(CompanyProfile.user_id == UUID(current_user.user_id))
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail='Company profile not found')
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    await db.commit()
    await db.refresh(row)
    return await get_company_profile_dict(db, current_user.user_id) or {}


@router.get('/me/ai-preferences')
async def get_ai_preferences(
    current_user: LiteUser,
    db: AsyncSession = Depends(get_db),
) -> dict:
    from ...core.personal_workspace import get_ai_preferences_dict
    from ...core.ai.lite_ai import resolve_default_model, resolve_default_provider

    await ensure_personal_workspace(db, current_user.user_id, current_user.email)
    prefs = await get_ai_preferences_dict(db, current_user.user_id)
    return {
        'provider': prefs.get('provider') or resolve_default_provider(),
        'model': prefs.get('model') or resolve_default_model(resolve_default_provider()),
        'style': prefs.get('style') or 'professional',
        'tone': prefs.get('tone') or 'formal',
        **prefs,
    }


@router.patch('/me/ai-preferences')
async def update_ai_preferences(
    body: AiPreferencesUpdate,
    current_user: LiteUser,
    db: AsyncSession = Depends(get_db),
) -> dict:
    from ...core.personal_workspace import update_ai_preferences_dict

    await ensure_personal_workspace(db, current_user.user_id, current_user.email)
    updated = await update_ai_preferences_dict(
        db,
        current_user.user_id,
        body.model_dump(exclude_unset=True),
    )
    from ...core.ai.lite_ai import resolve_default_model, resolve_default_provider

    return {
        'provider': updated.get('provider') or resolve_default_provider(),
        'model': updated.get('model') or resolve_default_model(resolve_default_provider()),
        'style': updated.get('style') or 'professional',
        'tone': updated.get('tone') or 'formal',
        **updated,
    }


@router.post('/change-password')
async def change_password(
    request: ChangePasswordRequest,
    current_user: LiteUser,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Change the signed-in user's database password (local auth)."""
    if (settings.AUTH_PROVIDER or 'local').strip().lower() != 'local':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Password change is only available for local database auth',
        )
    try:
        await change_user_password(
            db,
            user_id=current_user.user_id,
            current_password=request.current_password,
            new_password=request.new_password,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except OperationalError as exc:
        raise _database_unavailable(exc) from exc

    return {'message': 'Password updated successfully'}


@router.get('/owner-account-file', include_in_schema=False)
async def owner_account_file_hint() -> dict:
    """Where to read default system owner login (dev)."""
    path = owner_account_file_path()
    return {
        'path': str(path),
        'exists': path.is_file(),
        'hint': 'Open this file after run.bat for default system owner email and password',
    }


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
