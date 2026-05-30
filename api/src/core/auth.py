"""Authentication Service - JWT Management and Token Handling"""

from datetime import datetime, timedelta, timezone
from typing import Any, ClassVar, Optional

from uuid import uuid4

from .tenant_types import TenantId, UserId

import httpx
from jose import JWTError, jwt

from .config import settings
from .logging import get_logger
from .roles import normalize_membership_role

logger = get_logger('auth')


class TokenPayload:
    """JWT Token Payload"""

    def __init__(
        self,
        sub: str,
        exp: int,
        iat: int,
        jti: Optional[str] = None,
        email: Optional[str] = None,
        role: Optional[str] = None,
        tenant_id: Optional[str] = None,
        membership_role: Optional[str] = None,
    ):
        self.sub = sub
        self.exp = exp
        self.iat = iat
        self.jti = jti
        self.email = email
        self.role = role
        self.tenant_id = tenant_id
        self.membership_role = membership_role

    @classmethod
    def from_dict(cls, data: dict) -> 'TokenPayload':
        return cls(
            sub=data.get('sub', ''),
            exp=data.get('exp', 0),
            iat=data.get('iat', 0),
            jti=data.get('jti'),
            email=data.get('email'),
            role=data.get('role'),
            tenant_id=data.get('tenant_id'),
            membership_role=data.get('membership_role'),
        )


class AuthService:
    """Authentication service for JWT management"""

    _revoked_jtis: ClassVar[set[str]] = set()

    def __init__(self):
        self.secret_key = settings.JWT_SECRET
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS

    def create_access_token(
        self,
        user_id: str,
        email: Optional[str] = None,
        role: Optional[str] = None,
        tenant_id: Optional[str] = None,
        membership_role: Optional[str] = None,
    ) -> tuple[str, datetime]:
        """Create JWT access token"""
        jti = str(uuid4())
        iat = datetime.now(timezone.utc)
        exp = iat + timedelta(minutes=self.access_token_expire)

        payload = {
            'sub': user_id,
            'jti': jti,
            'iat': int(iat.timestamp()),
            'exp': int(exp.timestamp()),
            'type': 'access',
            'email': email,
            'role': role,
            'tenant_id': tenant_id,
            'membership_role': membership_role,
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token, exp

    def create_refresh_token(
        self,
        user_id: str,
        *,
        email: Optional[str] = None,
        role: Optional[str] = None,
        tenant_id: Optional[str] = None,
        membership_role: Optional[str] = None,
    ) -> tuple[str, datetime]:
        """Create refresh token (carries session claims for access token re-issue)."""
        jti = str(uuid4())
        iat = datetime.now(timezone.utc)
        exp = iat + timedelta(days=self.refresh_token_expire)

        payload = {
            'sub': user_id,
            'jti': jti,
            'iat': int(iat.timestamp()),
            'exp': int(exp.timestamp()),
            'type': 'refresh',
            'email': email,
            'role': role,
            'tenant_id': tenant_id,
            'membership_role': membership_role,
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token, exp

    def     revoke_token(self, jti: Optional[str], db=None) -> None:
        """Invalidate a token by jti (logout). Persisted to DB when db provided."""
        if not jti:
            return
        self._revoked_jtis.add(jti)
        if db is not None:
            try:
                from .models import RevokedToken, generate_uuid

                db.add(RevokedToken(id=generate_uuid(), jti=jti))
            except Exception:
                logger.exception('Failed to persist revoked token jti=%s', jti)

    def is_token_revoked(self, jti: Optional[str], db=None) -> bool:
        if not jti:
            return False
        if jti in self._revoked_jtis:
            return True
        if db is not None:
            try:
                from sqlalchemy import select
                from .models import RevokedToken

                result = db.execute(select(RevokedToken).where(RevokedToken.jti == jti).limit(1))
                found = result.scalar_one_or_none()
                if found:
                    self._revoked_jtis.add(jti)
                    return True
            except Exception:
                logger.exception('Failed to check revoked token jti=%s', jti)
        return False

    def verify_token(self, token: str, expected_type: Optional[str] = None) -> Optional[TokenPayload]:
        """Verify and decode JWT token, optionally checking the token type claim."""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )
            token_payload = TokenPayload.from_dict(payload)
            if self.is_token_revoked(token_payload.jti):
                logger.info('Rejected revoked token jti=%s', token_payload.jti)
                return None
            if expected_type and payload.get('type') != expected_type:
                logger.info('Rejected token with mismatched type (expected=%s, got=%s)', expected_type, payload.get('type'))
                return None
            return token_payload
        except JWTError as e:
            logger.warning(f'Token verification failed: {e}')
            return None

    def decode_token(self, token: str) -> Optional[dict]:
        """Decode token without verification (for debugging)"""
        try:
            return jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={'verify_signature': False},
            )
        except JWTError:
            return None

    def get_token_from_header(self, authorization: str) -> Optional[str]:
        """Extract token from Authorization header"""
        if not authorization:
            return None

        if not authorization.startswith('Bearer '):
            return None

        return authorization.replace('Bearer ', '')


class ClerkAuthService:
    """Clerk authentication service"""

    @staticmethod
    async def verify_token(token: str) -> Optional[dict]:
        """Verify Clerk JWT token"""
        if not settings.CLERK_SECRET_KEY:
            logger.warning('Clerk secret key not configured')
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    'https://api.clerk.com/v1/me',
                    headers={'Authorization': f'Bearer {token}'},
                    timeout=5.0,
                )

                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f'Clerk token verification failed: {e}')

        return None

    @staticmethod
    async def get_user(user_id: str) -> Optional[dict]:
        """Get Clerk user by ID"""
        if not settings.CLERK_SECRET_KEY:
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f'https://api.clerk.com/v1/users/{user_id}',
                    headers={'Authorization': f'Bearer {settings.CLERK_SECRET_KEY}'},
                    timeout=5.0,
                )

                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f'Failed to get Clerk user: {e}')

        return None


class AuthContext:
    """Authentication context with user info"""

    def __init__(
        self,
        user_id: UserId,
        email: Optional[str] = None,
        role: Optional[str] = None,
        tenant_id: Optional[TenantId] = None,
        membership_role: Optional[str] = None,
    ):
        self.user_id = user_id
        self.email = email
        self.role = role
        self.tenant_id = tenant_id
        self.membership_role = membership_role

    def to_dict(self) -> dict[str, Any]:
        return {
            'user_id': self.user_id,
            'email': self.email,
            'role': self.role,
            'tenant_id': self.tenant_id,
            'membership_role': self.membership_role,
        }

    def is_super_admin(self) -> bool:
        return self.role == 'super_admin'

    def is_tenant_admin(self) -> bool:
        effective = normalize_membership_role(self.membership_role) or normalize_membership_role(self.role)
        return effective in ('owner', 'admin')

    def can_access_tenant(self, tenant_id: str) -> bool:
        if self.is_super_admin():
            return True
        return self.tenant_id == tenant_id


auth_service = AuthService()