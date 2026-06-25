"""Auth module — models, session, AuthBackend, PermissionChecker, dependencies."""

from __future__ import annotations

from fastapi_console.auth.backend import AuthBackend, BuiltinAuthBackend
from fastapi_console.auth.csrf import (
    auth_redirect_handler,
    require_csrf_token,
    set_csrf_cookie,
)
from fastapi_console.auth.models import (
    AdminFieldPermission,
    AdminPermission,
    AdminRole,
    AdminUser,
)
from fastapi_console.auth.session import SessionBackend, SignedCookieSessionBackend

__all__ = [
    "AdminFieldPermission",
    "AdminPermission",
    "AdminRole",
    "AdminUser",
    "AuthBackend",
    "BuiltinAuthBackend",
    "SessionBackend",
    "SignedCookieSessionBackend",
    "auth_redirect_handler",
    "require_csrf_token",
    "set_csrf_cookie",
]
