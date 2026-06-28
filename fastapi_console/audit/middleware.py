"""Audit middleware — sets and clears audit context from the request."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Request, Response

from fastapi_console.audit.context import clear_audit_context, set_audit_context


async def audit_context_middleware(request: Request, call_next: Callable) -> Response:
    """Middleware to set audit context from the request and clear it after.

    Sets IP address and user-agent before the handler runs.  The user
    identity (user_id, user_email) is added later by
    :func:`fastapi_console.auth.identity.resolve_user` once the auth
    dependency resolves the current user — which always happens before
    any ``session.commit()`` that would trigger audit listeners.
    """
    context_data: dict = {}

    if request.client is not None:
        context_data["ip_address"] = request.client.host

    user_agent = request.headers.get("user-agent")
    if user_agent:
        context_data["user_agent"] = user_agent

    if context_data:
        set_audit_context(context_data)

    response = await call_next(request)

    clear_audit_context()

    return response