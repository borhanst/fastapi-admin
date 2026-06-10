"""Audit middleware — sets and clears audit context from the request."""

from __future__ import annotations

from typing import Callable

from fastapi import Request, Response
from starlette.types import ASGIApp

from fastapi_admin.audit.context import clear_audit_context, set_audit_context


async def audit_context_middleware(request: Request, call_next: Callable) -> Response:
    """Middleware to set audit context from the request and clear it after.
    
    Reads:
        - request.state.admin_user (should be an instance of the auth model)
        - request.client.host (for IP address)
        - request.headers.get("user-agent") (for user agent)
    
    Sets the audit context with:
        - user_id: the admin user's ID
        - user_email: the admin user's email
        - ip_address: the client's IP address
        - user_agent: the user agent string
    
    The context is cleared after the response is sent.
    """
    # Set audit context
    admin_user = getattr(request.state, "admin_user", None)
    context_data = {}
    if admin_user is not None:
        # Assuming the admin user has an 'id' and 'email' attribute
        context_data["user_id"] = getattr(admin_user, "id", None)
        context_data["user_email"] = getattr(admin_user, "email", None)
    
    # IP address
    if request.client is not None:
        context_data["ip_address"] = request.client.host
    
    # User agent
    user_agent = request.headers.get("user-agent")
    if user_agent:
        context_data["user_agent"] = user_agent
    
    if context_data:
        set_audit_context(context_data)
    
    # Process the request
    response = await call_next(request)
    
    # Clear the context after the response is sent
    clear_audit_context()
    
    return response