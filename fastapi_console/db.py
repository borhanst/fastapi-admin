"""Per-request database session management.

Replaces the single shared ``AsyncSession`` on ``app.state`` with a
``sessionmaker`` factory and ASGI middleware that creates + tears down
a fresh session for every incoming request.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


def create_session_factory(
    engine: Any,
) -> async_sessionmaker[AsyncSession]:
    """Create an ``async_sessionmaker`` bound to *engine*."""
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


def get_db_session(request: Request) -> AsyncSession:
    """Return the per-request ``AsyncSession``.

    The session is created by :class:`SessionMiddleware` and stored on
    ``request.state.admin_db_session``.  Falls back to the legacy
    ``app.state.admin_db_session`` when the middleware is not active (e.g.
    in tests).
    """
    session = getattr(request.state, "admin_db_session", None)
    if session is not None:
        return session
    # Backward-compat: legacy single session on app.state
    return request.app.state.admin_db_session


class SessionMiddleware(BaseHTTPMiddleware):
    """Create a new ``AsyncSession`` per request and close it afterwards.

    The session factory is read from ``app.state.admin_session_factory``.
    On each request a fresh session is opened; it is **committed** when the
    response status is 2xx and **rolled back** otherwise, then always closed.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        factory: async_sessionmaker | None = getattr(
            request.app.state, "admin_session_factory", None
        )
        if factory is None:
            # No factory configured — fall through to legacy behaviour.
            return await call_next(request)

        async with factory() as session:
            request.state.admin_db_session = session  # type: ignore[attr-defined]
            response = await call_next(request)

            if 200 <= response.status_code < 400:
                await session.commit()
                # Write buffered audit log entries that were collected during
                # the sync after_flush event (to avoid MissingGreenlet).
                try:
                    from fastapi_console.audit.listener import flush_audit_entries
                    await flush_audit_entries(session)
                    await session.commit()
                except Exception:
                    pass
            else:
                await session.rollback()

        return response
