"""Views package — re-exports ModelAdmin and route factories."""
from fastapi_admin.modeladmin import ModelAdmin
from fastapi_admin.views.list import list_view_factory
from fastapi_admin.views.form import (
    create_form_factory,
    create_submit_factory,
    edit_form_factory,
    edit_submit_factory,
)
from fastapi_admin.views.delete import delete_factory
from fastapi_admin.views.bulk import bulk_factory
from fastapi_admin.views.search import search_factory

__all__ = [
    "ModelAdmin",
    "list_view_factory",
    "create_form_factory",
    "create_submit_factory",
    "edit_form_factory",
    "edit_submit_factory",
    "delete_factory",
    "bulk_factory",
    "search_factory",
]
