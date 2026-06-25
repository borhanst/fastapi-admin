"""Create and edit form handler factories."""

from __future__ import annotations

from fastapi_admin.registry import RegisteredModel


def create_form_factory(registered: RegisteredModel):
    """Create a form display handler using ViewFactory internally.

    This function maintains backward compatibility while delegating
    to the new ViewFactory for view creation.
    """
    from fastapi_admin.views.factory import ViewFactory

    factory = ViewFactory()
    return factory.create_create_form_view(registered)


def create_submit_factory(registered: RegisteredModel):
    """Create a form submission handler using ViewFactory internally.

    This function maintains backward compatibility while delegating
    to the new ViewFactory for view creation.
    """
    from fastapi_admin.views.factory import ViewFactory

    factory = ViewFactory()
    return factory.create_create_submit_view(registered)


def edit_form_factory(registered: RegisteredModel):
    """Create an edit form display handler using ViewFactory internally.

    This function maintains backward compatibility while delegating
    to the new ViewFactory for view creation.
    """
    from fastapi_admin.views.factory import ViewFactory

    factory = ViewFactory()
    return factory.create_edit_form_view(registered)


def edit_submit_factory(registered: RegisteredModel):
    """Create an edit form submission handler using ViewFactory internally.

    This function maintains backward compatibility while delegating
    to the new ViewFactory for view creation.
    """
    from fastapi_admin.views.factory import ViewFactory

    factory = ViewFactory()
    return factory.create_edit_submit_view(registered)
