"""Views package — re-exports ModelAdmin and route factories."""
from fastapi_admin.modeladmin import ModelAdmin
from fastapi_admin.views.bulk import bulk_factory
from fastapi_admin.views.context import DisplayColumn, ViewContextBuilder
from fastapi_admin.views.delete import delete_factory
from fastapi_admin.views.factory import ViewFactory
from fastapi_admin.views.form import (
    create_form_factory,
    create_submit_factory,
    edit_form_factory,
    edit_submit_factory,
)
from fastapi_admin.views.list import list_view_factory
from fastapi_admin.views.search import search_factory
from fastapi_admin.views.sidebar import inject_sidebar_context


def create_model_router(registered):
    """Create a model router - backward compatible wrapper around build_model_router."""
    from fastapi_admin.router import build_model_router
    return build_model_router(registered)

__all__ = [
    "ModelAdmin",
    "ViewContextBuilder",
    "ViewFactory",
    "DisplayColumn",
    "inject_sidebar_context",
    "list_view_factory",
    "create_form_factory",
    "create_submit_factory",
    "edit_form_factory",
    "edit_submit_factory",
    "delete_factory",
    "bulk_factory",
    "search_factory",
    "create_model_router",
]
