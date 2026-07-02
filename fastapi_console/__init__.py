"""FastAPI Console — Drop-in admin panel for FastAPI + SQLAlchemy apps."""

from fastapi_console.admin import Admin
from fastapi_console.admin.decorators import column
from fastapi_console.exceptions import ConfigError
from fastapi_console.nav import (
    BuiltNavGroup,
    BuiltNavItem,
    DefaultSidebarBuilder,
    NavGroupConfig,
    NavItemConfig,
    SidebarBuilder,
)
from fastapi_console.registry import AdminRegistry, RegisteredModel
from fastapi_console.types import (
    ColumnMeta,
    ExtraField,
    FieldMeta,
    FieldRenderContext,
    FieldsetContext,
    FieldsetSpec,
    FormContext,
    PermissionSet,
    RelationMeta,
    SeedRole,
)
from fastapi_console.views import (
    AdminExtra,
    BaseView,
    BulkView,
    CreateView,
    DeleteView,
    EditView,
    ListView,
    ModelAdmin,
    SearchView,
)

__all__ = [
    "Admin",
    "AdminRegistry",
    "ConfigError",
    "RegisteredModel",
    "ModelAdmin",
    "column",
    "BuiltNavGroup",
    "BuiltNavItem",
    "DefaultSidebarBuilder",
    "NavGroupConfig",
    "NavItemConfig",
    "SidebarBuilder",
    "ColumnMeta",
    "RelationMeta",
    "FieldMeta",
    "PermissionSet",
    "SeedRole",
    "ExtraField",
    "FieldRenderContext",
    "FieldsetContext",
    "FieldsetSpec",
    "FormContext",
    # View classes
    "BaseView",
    "ListView",
    "CreateView",
    "EditView",
    "DeleteView",
    "BulkView",
    "SearchView",
    # Per-model assets
    "AdminExtra",
]
__version__ = "0.1.8"
