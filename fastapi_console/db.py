"""Per-request database session management.

Replaces the single shared ``AsyncSession`` on ``app.state`` with a
``sessionmaker`` factory and ASGI middleware that creates + tears down
a fresh session for every incoming request.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from starlette.requests import Request


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
    ``scope["state"]["admin_db_session"]`` (accessible via
    ``request.state.admin_db_session``).  Falls back to the legacy
    ``app.state.admin_db_session`` when the middleware is not active.
    """
    session = getattr(request.state, "admin_db_session", None)
    if session is not None:
        return session
    return request.app.state.admin_db_session


class SessionMiddleware:
    """Pure ASGI middleware — one session per request, one commit or rollback.

    The session factory is read from ``app.state.admin_session_factory``
    at request time (it is not available when middleware is registered).
    On success the session is committed.  On exception it is rolled back.
    The session is always closed when the request completes.
    """

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        from starlette.datastructures import State

        state: State = scope.get("state", State())  # type: ignore[assignment]
        factory = getattr(state, "admin_session_factory", None) or getattr(
            self.app.state, "admin_session_factory", None
        )
        if factory is None:
            await self.app(scope, receive, send)
            return

        async with factory() as session:
            scope["state"]["admin_db_session"] = session  # type: ignore[attr-defined]
            try:
                await self.app(scope, receive, send)
            except Exception:
                await session.rollback()
                raise
            else:
                await session.commit()
