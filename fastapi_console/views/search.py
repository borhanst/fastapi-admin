"""Search endpoint factory for FK/M2M relation pickers.

Backward-compatible wrapper — delegates to SearchView class.
"""

from __future__ import annotations

from typing import Any

from fastapi import Request
<<<<<<< HEAD:fastapi_console/views/search.py
from sqlalchemy import String, or_, select

from fastapi_console.registry import RegisteredModel
=======

from fastapi_admin.registry import RegisteredModel
>>>>>>> 6fbbaad1ffffd156930439440a97eefaf7f5c603:fastapi_admin/views/search.py


def search_factory(registered: RegisteredModel):
    """Create a search handler — delegates to SearchView.html_response."""
    from fastapi_admin.views.class_views import SearchView, _resolve_view_class

    view_class = _resolve_view_class(registered.admin, "search_view_class", SearchView)
    view_instance = view_class(registered)

    async def _handler(request: Request, **kwargs: Any):
        return await view_instance.html_response(request, **kwargs)

    _handler.__name__ = f"search_{registered.table_name}"
    return _handler
