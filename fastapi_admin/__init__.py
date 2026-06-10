"""FastAPI Admin — Drop-in admin panel for FastAPI + SQLAlchemy apps."""

from fastapi_admin.admin import Admin
from fastapi_admin.exceptions import ConfigError
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
from fastapi_admin.views import ModelAdmin

__all__ = [
    "Admin",
    "AdminRegistry",
    "ConfigError",
    "RegisteredModel",
    "ModelAdmin",
    "ColumnMeta",
    "RelationMeta",
    "FieldMeta",
    "PermissionSet",
    "FieldsetSpec",
    "SeedRole",
    "ExtraField",
    "FieldRenderContext",
    "FieldsetContext",
    "FormContext",
]
__version__ = "0.1.0"
