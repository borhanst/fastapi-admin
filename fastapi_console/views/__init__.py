"""Views package — re-exports ModelAdmin and route factories."""
from fastapi_console.modeladmin import ModelAdmin
from fastapi_console.views.list import list_view_factory
from fastapi_console.views.form import (
    create_form_factory,
    create_submit_factory,
    edit_form_factory,
    edit_submit_factory,
)
from fastapi_console.views.delete import delete_factory
from fastapi_console.views.bulk import bulk_factory
from fastapi_console.views.search import search_factory
from fastapi_console.views.sidebar import inject_sidebar_context

__all__ = [
    "ModelAdmin",
    "inject_sidebar_context",
    "list_view_factory",
    "create_form_factory",
    "create_submit_factory",
    "edit_form_factory",
    "edit_submit_factory",
    "delete_factory",
    "bulk_factory",
    "search_factory",
]
