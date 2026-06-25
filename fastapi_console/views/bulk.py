"""Bulk action handler factory for registered models.

Backward-compatible wrapper — delegates to BulkView class.
"""

from __future__ import annotations

from typing import Any

from fastapi import Request

<<<<<<< HEAD:fastapi_console/views/bulk.py
from fastapi_console.flash import add_flash
from fastapi_console.registry import RegisteredModel
=======
from fastapi_admin.registry import RegisteredModel
>>>>>>> 6fbbaad1ffffd156930439440a97eefaf7f5c603:fastapi_admin/views/bulk.py


def bulk_factory(registered: RegisteredModel):
    """Create a bulk action handler — delegates to BulkView.html_response."""
    from fastapi_admin.views.class_views import BulkView, _resolve_view_class

    view_class = _resolve_view_class(registered.admin, "bulk_view_class", BulkView)
    view_instance = view_class(registered)

    async def _handler(request: Request, **kwargs: Any):
        return await view_instance.html_response(request, **kwargs)

    _handler.__name__ = f"bulk_{registered.table_name}"
    return _handler
