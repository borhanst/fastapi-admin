"""Delete handler factory for registered models."""

from __future__ import annotations

from fastapi_admin.registry import RegisteredModel


def delete_factory(registered: RegisteredModel):
    """Create a delete handler using ViewFactory internally.

    This function maintains backward compatibility while delegating
    to the new ViewFactory for view creation.
    """
    from fastapi_admin.views.factory import ViewFactory

    factory = ViewFactory()
    return factory.create_delete_view(registered)
