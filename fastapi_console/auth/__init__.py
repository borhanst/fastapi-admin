"""Auth module — models, session, AuthBackend, PermissionChecker, dependencies."""

from __future__ import annotations

<<<<<<< HEAD:fastapi_console/auth/__init__.py
from fastapi_console.auth.backend import AuthBackend, BuiltinAuthBackend
from fastapi_console.auth.models import (
=======
from fastapi_admin.auth.backend import AuthBackend, BuiltinAuthBackend
from fastapi_admin.auth.csrf import (
    auth_redirect_handler,
    require_csrf_token,
    set_csrf_cookie,
)
from fastapi_admin.auth.models import (
>>>>>>> 6fbbaad1ffffd156930439440a97eefaf7f5c603:fastapi_admin/auth/__init__.py
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
