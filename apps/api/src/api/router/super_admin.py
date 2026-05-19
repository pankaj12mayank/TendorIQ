"""Super Admin Authentication - Direct Login with .env credentials"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel
from jose import jwt, JWTError

from ...core.config import settings
from ...core.auth import AuthContext
from ...core.database import get_db
from ..dependencies.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/auth', tags=['Authentication'])


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    message: str
    user: Optional[dict] = None
    token: Optional[str] = None


class MeResponse(BaseModel):
    user_id: str
    email: str
    role: str
    is_super_admin: bool
    permissions: list


def verify_super_admin_credentials(email: str, password: str) -> bool:
    """Verify credentials from .env"""
    
    if not settings.SUPER_ADMIN_EMAIL or not settings.SUPER_ADMIN_PASSWORD:
        logger.warning("Super Admin credentials not configured in .env")
        return False
    
    return (
        email.lower() == settings.SUPER_ADMIN_EMAIL.lower() and 
        password == settings.SUPER_ADMIN_PASSWORD
    )


def create_super_admin_token(email: str) -> str:
    """Create JWT token for super admin"""
    
    payload = {
        'sub': 'super_admin',
        'email': email,
        'role': 'super_admin',
        'type': 'super_admin_token',
        'iat': datetime.utcnow().timestamp(),
        'exp': (datetime.utcnow() + timedelta(days=7)).timestamp(),
    }
    
    return jwt.encode(payload, settings.JWT_SECRET, algorithm='HS256')


@router.post('/login', response_model=LoginResponse)
async def login(
    request: LoginRequest,
    authorization: Optional[str] = Header(None)
):
    """Login with email/password (Super Admin from .env OR Clerk)"""
    
    # Check if Super Admin credentials
    if verify_super_admin_credentials(request.email, request.password):
        logger.info(f"Super Admin login successful: {request.email}")
        
        token = create_super_admin_token(request.email)
        
        return LoginResponse(
            success=True,
            message="Login successful as Super Admin",
            user={
                "email": request.email,
                "role": "super_admin",
                "is_super_admin": True,
            },
            token=token
        )
    
    # Otherwise check if Clerk auth token provided
    if authorization and authorization.startswith('Bearer '):
        # This would verify Clerk token
        return LoginResponse(
            success=True,
            message="Clerk authentication used",
            user={
                "email": request.email,
                "role": "user",
                "is_super_admin": False,
            }
        )
    
    # Invalid credentials
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password"
    )


@router.get('/me', response_model=MeResponse)
async def get_me(current_user: AuthContext = Depends(get_current_user)):
    """Get current user info"""
    
    is_super_admin = (
        current_user.role == 'super_admin' or 
        (current_user.email and current_user.email.lower() == settings.SUPER_ADMIN_EMAIL.lower())
    )
    
    # Get all permissions for super admin
    permissions = []
    if is_super_admin:
        permissions = [
            "tender:*",
            "bid:*", 
            "document:*",
            "org:*",
            "user:*",
            "settings:*",
            "analytics:*",
            "ai:*",
            "api:*",
            "billing:*",
            "admin:*",
        ]
    
    return MeResponse(
        user_id=current_user.user_id or "super_admin",
        email=current_user.email or settings.SUPER_ADMIN_EMAIL,
        role=current_user.role or "super_admin",
        is_super_admin=is_super_admin,
        permissions=permissions
    )


@router.get('/status')
async def auth_status():
    """Check authentication status and Super Admin config"""
    
    super_admin_configured = bool(settings.SUPER_ADMIN_EMAIL and settings.SUPER_ADMIN_PASSWORD)
    
    return {
        "super_admin_configured": super_admin_configured,
        "super_admin_email": settings.SUPER_ADMIN_EMAIL if super_admin_configured else None,
        "stripe_configured": bool(settings.STRIPE_SECRET_KEY),
        "razorpay_configured": bool(settings.RAZORPAY_KEY_ID),
        "message": "Super Admin login available" if super_admin_configured else "Configure SUPER_ADMIN_EMAIL and SUPER_ADMIN_PASSWORD in .env"
    }


router_login = router

__all__ = ['router']