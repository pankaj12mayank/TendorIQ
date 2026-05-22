"""Re-export shim — auth routes consolidated into routers/auth.py.

All login/me/status logic moved to apps/api/src/api/routers/auth.py.
This module kept for backward compatibility during transition.
"""

from ...core.local_auth import issue_access_token
from ..routers.auth import (
    router,
    login,
    auth_status,
    get_token,
    refresh_token,
    get_current_user_info,
    logout,
    clerk_webhook,
    LoginRequest,
    LoginResponse,
    TokenResponse,
    UserResponse,
    RefreshTokenRequest,
    WebhookPayload,
    verify_super_admin_credentials,
    verify_demo_user_credentials,
)

# Backward-compatible alias
create_auth_token = issue_access_token

__all__ = [
    'router',
    'login',
    'auth_status',
    'get_token',
    'refresh_token',
    'get_current_user_info',
    'logout',
    'clerk_webhook',
]
