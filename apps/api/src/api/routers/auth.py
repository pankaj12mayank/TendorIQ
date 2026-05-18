"""Authentication API Router"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from ..dependencies.auth import get_current_user, CurrentUser
from ...core.auth import AuthService, AuthContext
from ...core.logging import get_logger

logger = get_logger('auth_api')

router = APIRouter(prefix='/auth', tags=['Authentication'])


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


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class WebhookPayload(BaseModel):
    type: str
    data: dict


@router.post('/token', response_model=TokenResponse)
async def login(
    user: CurrentUser,
) -> dict:
    """Get access and refresh tokens for authenticated user"""
    auth_service = AuthService()

    access_token, access_exp = auth_service.create_access_token(
        user_id=user.user_id,
        email=user.email,
        role=user.role,
        tenant_id=user.tenant_id,
    )

    refresh_token, refresh_exp = auth_service.create_refresh_token(
        user_id=user.user_id,
    )

    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'expires_in': int((access_exp - auth_service).total_seconds()),
        'token_type': 'bearer',
    }


@router.post('/refresh', response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest) -> dict:
    """Refresh access token using refresh token"""
    auth_service = AuthService()

    payload = auth_service.verify_token(request.refresh_token)

    if not payload or payload.exp < datetime.utcnow().timestamp():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid or expired refresh token',
        )

    access_token, access_exp = auth_service.create_access_token(
        user_id=payload.sub,
        email=payload.email,
        role=payload.role,
        tenant_id=payload.tenant_id,
    )

    return {
        'access_token': access_token,
        'refresh_token': request.refresh_token,
        'expires_in': int((access_exp - datetime.utcnow()).total_seconds()),
        'token_type': 'bearer',
    }


@router.get('/me', response_model=UserResponse)
async def get_current_user_info(current_user: CurrentUser) -> dict:
    """Get current user information"""
    return {
        'id': current_user.user_id,
        'email': current_user.email or '',
        'name': None,
        'role': current_user.role,
        'tenant_id': current_user.tenant_id,
    }


@router.post('/logout')
async def logout(current_user: CurrentUser) -> dict:
    """Logout user (invalidate tokens server-side if needed)"""
    logger.info('User logged out', user_id=current_user.user_id)
    return {'message': 'Logged out successfully'}


@router.post('/clerk/webhook')
async def clerk_webhook(payload: WebhookPayload) -> dict:
    """Handle Clerk webhooks"""
    logger.info('Clerk webhook received', type=payload.type)

    if payload.type == 'user.created':
        logger.info('New user created via Clerk', user_id=payload.data.get('id'))
    elif payload.type == 'user.updated':
        logger.info('User updated via Clerk', user_id=payload.data.get('id'))
    elif payload.type == 'user.deleted':
        logger.info('User deleted via Clerk', user_id=payload.data.get('id'))

    return {'status': 'received'}


from datetime import datetime