"""Super Admin Authentication - Direct Login with .env credentials"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel
from jose import jwt, JWTError

from ...core.config import get_settings
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
    """Verify super admin credentials from .env (fresh read each login)."""
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
    """Optional demo tenant user for local dev (role from .env, no per-role API keys)."""
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


def create_auth_token(email: str, role: str, sub: Optional[str] = None) -> str:
    """Create JWT for any role — permissions enforced server-side by role."""
    payload = {
        'sub': sub or email,
        'email': email,
        'role': role,
        'type': 'access_token',
        'iat': datetime.utcnow().timestamp(),
        'exp': (datetime.utcnow() + timedelta(days=7)).timestamp(),
    }
    return jwt.encode(payload, get_settings().JWT_SECRET, algorithm='HS256')


@router.post('/login', response_model=LoginResponse)
async def login(
    request: LoginRequest,
    authorization: Optional[str] = Header(None)
):
    """Unified email/password login — role comes from account, not API keys."""

    if verify_super_admin_credentials(request.email, request.password):
        logger.info("Login successful: super_admin %s", request.email)
        token = create_auth_token(request.email, 'super_admin', sub='super_admin')
        return LoginResponse(
            success=True,
            message="Login successful",
            user={
                "email": request.email,
                "name": "Super Admin",
                "role": "super_admin",
                "is_super_admin": True,
            },
            token=token,
        )

    demo = verify_demo_user_credentials(request.email, request.password)
    if demo:
        logger.info("Login successful: %s role=%s", demo['email'], demo['role'])
        token = create_auth_token(demo['email'], demo['role'])
        return LoginResponse(
            success=True,
            message="Login successful",
            user={
                "email": demo['email'],
                "name": demo['name'],
                "role": demo['role'],
                "is_super_admin": False,
            },
            token=token,
        )

    if authorization and authorization.startswith('Bearer '):
        return LoginResponse(
            success=True,
            message="Clerk authentication used",
            user={
                "email": request.email,
                "role": "user",
                "is_super_admin": False,
            },
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
    )


@router.get('/me', response_model=MeResponse)
async def get_me(current_user: AuthContext = Depends(get_current_user)):
    """Get current user info"""
    
    s = get_settings()
    is_super_admin = (
        current_user.role == 'super_admin'
        or (
            current_user.email
            and current_user.email.lower() == (s.SUPER_ADMIN_EMAIL or '').strip().lower()
        )
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
        email=current_user.email or s.SUPER_ADMIN_EMAIL,
        role=current_user.role or "super_admin",
        is_super_admin=is_super_admin,
        permissions=permissions
    )


@router.get('/status')
async def auth_status():
    """Check authentication status and Super Admin config"""
    
    s = get_settings()
    super_admin_configured = bool(
        (s.SUPER_ADMIN_EMAIL or '').strip() and (s.SUPER_ADMIN_PASSWORD or '').strip()
    )

    return {
        "super_admin_configured": super_admin_configured,
        "super_admin_email": s.SUPER_ADMIN_EMAIL.strip() if super_admin_configured else None,
        "demo_user_configured": bool((s.DEMO_USER_EMAIL or '').strip()),
        "message": (
            "Sign in at /sign-in with SUPER_ADMIN_* or DEMO_USER_* from .env"
            if super_admin_configured
            else "Configure SUPER_ADMIN_EMAIL and SUPER_ADMIN_PASSWORD in .env"
        ),
    }


router_login = router

__all__ = ['router']