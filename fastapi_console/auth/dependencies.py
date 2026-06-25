"""FastAPI dependencies — session, current user, permission checker."""

from __future__ import annotations

from typing import Any

from fastapi import Depends, HTTPException, Request
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from fastapi_console.auth.protocol import AdminUserProtocol
from fastapi_console.auth.session import SignedCookieSessionBackend


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------


def _get_session_backend(request: Request) -> SignedCookieSessionBackend:
    """Resolve the session backend from app state (set during admin setup)."""
    backend: SignedCookieSessionBackend | None = getattr(
        request.app.state, "admin_session_backend", None
    )
    if backend is None:
        raise HTTPException(
            status_code=500,
            detail="Admin session backend not initialised.",
        )
    return backend


def _get_sync_engine(request: Request):
    """Get or create a sync engine from the async engine in app.state."""
    from sqlalchemy.ext.asyncio import AsyncEngine

    async_engine = getattr(request.app.state, "admin_engine", None)
    if async_engine is None:
        raise HTTPException(
            status_code=500,
            detail="Admin database engine not initialised.",
        )

    # If it's already a sync engine, use it directly
    if not isinstance(async_engine, AsyncEngine):
        return async_engine

    # Extract the URL and create a sync engine
    sync_url = str(async_engine.url).replace("+aiosqlite", "").replace("+asyncpg", "").replace("+asyncmy", "")
    if not hasattr(request.app.state, "_admin_sync_engine"):
        request.app.state._admin_sync_engine = create_engine(sync_url, echo=False)
    return request.app.state._admin_sync_engine


def _get_db_session(request: Request) -> Session:
    """Yield a synchronous SQLAlchemy session.

    Works with both sync and async engines by creating a sync engine
    from the async URL when needed.
    """
    engine = _get_sync_engine(request)
    session = Session(bind=engine)
    try:
        yield session  # type: ignore[misc]
    finally:
        session.close()  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Per-request dependencies
# ---------------------------------------------------------------------------


def get_session(request: Request) -> dict[str, Any] | None:
    """Read and decode the admin session cookie from the current request."""
    session_backend = _get_session_backend(request)
    token = request.cookies.get(session_backend.cookie_name)
    return session_backend.decode(token)


async def get_current_admin_user(
    request: Request,
    session: Session = Depends(_get_db_session),
    session_payload: dict[str, Any] | None = Depends(get_session),
) -> AdminUserProtocol:
    """Resolve the logged-in admin user from the session cookie.

    Raises ``401`` if the session is missing, invalid, or the user is
    no longer active.
    """
    if session_payload is None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated. Please log in.",
        )

    user_id = session_payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid session payload.")

    auth_backend = getattr(request.app.state, "admin_auth_backend", None)
    if auth_backend is None:
        raise HTTPException(
            status_code=500,
            detail="Admin auth backend not initialised.",
        )

    user = await auth_backend.get_user(user_id, session)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive.")

    return user


async def get_permission_checker(
    user: AdminUserProtocol = Depends(get_current_admin_user),
    session: Session = Depends(_get_db_session),
) -> Any:
    """Build a ``PermissionChecker`` for the current user.

    The concrete ``PermissionChecker`` class is imported here to avoid
    circular imports (it will be implemented in Phase 8).
    """
    from fastapi_console.auth.permissions import PermissionChecker

    return PermissionChecker(session=session, user=user)


def require_permission(table_name: str, action: str):  # type: ignore[no-untyped-def]
    """Return a FastAPI dependency that enforces a permission check.

    Usage::

        @router.get("/")
        async def list_view(_=Depends(require_permission("products", "view"))):
            ...
    """

    async def _check(
        checker: Any = Depends(get_permission_checker),
    ) -> None:
        if not checker.has_permission(table_name, action):
            raise HTTPException(
                status_code=403,
                detail=f"You do not have permission to {action} {table_name}.",
            )

    return _check
