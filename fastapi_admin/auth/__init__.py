"""Auth module — models, session, AuthBackend, PermissionChecker, dependencies."""

from __future__ import annotations

from fastapi_admin.auth.backend import AuthBackend, BuiltinAuthBackend
from fastapi_admin.auth.csrf import require_csrf_token, set_csrf_cookie
from fastapi_admin.auth.models import (
    AdminFieldPermission,
    AdminPermission,
    AdminRole,
    AdminUser,
)
from fastapi_admin.auth.session import SessionBackend, SignedCookieSessionBackend

__all__ = [
    "AdminFieldPermission",
    "AdminPermission",
    "AdminRole",
    "AdminUser",
    "AuthBackend",
    "BuiltinAuthBackend",
    "SessionBackend",
    "SignedCookieSessionBackend",
    "require_csrf_token",
    "set_csrf_cookie",
]
