"""Create and edit form handler factories.

Backward-compatible wrappers — delegate to CreateView/EditView classes.
"""

from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi_admin.registry import RegisteredModel


def create_form_factory(registered: RegisteredModel):
    """Create form display handler — delegates to CreateView.html_response."""
    from fastapi_admin.views.class_views import CreateView, _resolve_view_class

    view_class = _resolve_view_class(registered.admin, "create_view_class", CreateView)
    view_instance = view_class(registered)

    async def _handler(request: Request, **kwargs: Any):
        return await view_instance.html_response(request, **kwargs)

    _handler.__name__ = f"create_form_{registered.table_name}"
    return _handler


def create_submit_factory(registered: RegisteredModel):
    """Create form submission handler — delegates to CreateView.html_response."""
    from fastapi_admin.views.class_views import CreateView, _resolve_view_class

    view_class = _resolve_view_class(registered.admin, "create_view_class", CreateView)
    view_instance = view_class(registered)

    async def _handler(request: Request, **kwargs: Any):
        return await view_instance.html_response(request, **kwargs)

    _handler.__name__ = f"create_submit_{registered.table_name}"
    return _handler


def edit_form_factory(registered: RegisteredModel):
    """Edit form display handler — delegates to EditView.html_response."""
    from fastapi_admin.views.class_views import EditView, _resolve_view_class

    view_class = _resolve_view_class(registered.admin, "edit_view_class", EditView)
    view_instance = view_class(registered)

    async def _handler(request: Request, **kwargs: Any):
        return await view_instance.html_response(request, **kwargs)

    _handler.__name__ = f"edit_form_{registered.table_name}"
    return _handler


def edit_submit_factory(registered: RegisteredModel):
    """Edit form submission handler — delegates to EditView.html_response."""
    from fastapi_admin.views.class_views import EditView, _resolve_view_class

    view_class = _resolve_view_class(registered.admin, "edit_view_class", EditView)
    view_instance = view_class(registered)

    async def _handler(request: Request, **kwargs: Any):
        return await view_instance.html_response(request, **kwargs)

    _handler.__name__ = f"edit_submit_{registered.table_name}"
    return _handler
