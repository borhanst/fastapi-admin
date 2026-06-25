"""FastAPI Console — Drop-in admin panel for FastAPI + SQLAlchemy apps."""

from fastapi_console.admin import Admin
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
from fastapi_console.views import ModelAdmin

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
]
__version__ = "0.1.5"
