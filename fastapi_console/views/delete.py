"""Delete handler factory for registered models.

Backward-compatible wrapper — delegates to DeleteView class.
"""

from __future__ import annotations

from typing import Any

from fastapi import Request

<<<<<<< HEAD:fastapi_console/views/delete.py
from fastapi_console.flash import add_flash
from fastapi_console.registry import RegisteredModel
=======
from fastapi_admin.registry import RegisteredModel
>>>>>>> 6fbbaad1ffffd156930439440a97eefaf7f5c603:fastapi_admin/views/delete.py


def delete_factory(registered: RegisteredModel):
    """Create a delete handler — delegates to DeleteView.html_response."""
    from fastapi_admin.views.class_views import DeleteView, _resolve_view_class

    view_class = _resolve_view_class(registered.admin, "delete_view_class", DeleteView)
    view_instance = view_class(registered)

    async def _handler(request: Request, **kwargs: Any):
        return await view_instance.html_response(request, **kwargs)

    _handler.__name__ = f"delete_{registered.table_name}"
    return _handler
