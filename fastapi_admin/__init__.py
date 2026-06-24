"""FastAPI Admin — Drop-in admin panel for FastAPI + SQLAlchemy apps."""

from fastapi_admin.admin import Admin
from fastapi_admin.exceptions import ConfigError
from fastapi_admin.nav import (
    BuiltNavGroup,
    BuiltNavItem,
    DefaultSidebarBuilder,
    NavGroupConfig,
    NavItemConfig,
    SidebarBuilder,
)
from fastapi_admin.registry import AdminRegistry, RegisteredModel
from fastapi_admin.types import (
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
from fastapi_admin.views import (
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
__version__ = "0.1.0"
