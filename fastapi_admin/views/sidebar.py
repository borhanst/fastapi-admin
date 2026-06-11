"""Sidebar context helper for template views."""

from __future__ import annotations

from typing import Any

from fastapi import Request


def inject_sidebar_context(request: Request, context: dict[str, Any]) -> dict[str, Any]:
    """Inject nav_groups + permissions_map into a template context dict."""
    admin_instance: Any = request.app.state.admin
    if hasattr(admin_instance, "build_sidebar_context"):
        user = getattr(request.state, "admin_user", None)
        context.update(admin_instance.build_sidebar_context(request, user=user))
    return context
