"""Core data structures for FastAPI Admin — ColumnMeta, RelationMeta, FieldMeta, etc."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ColumnMeta:
    """Metadata for a single SQLAlchemy column."""

    name: str
    type: Any  # SQLAlchemy type instance
    nullable: bool = True
    primary_key: bool = False
    foreign_keys: list = field(default_factory=list)
    default: Any = None
    server_default: Any = None
    index: bool = False
    unique: bool = False

    @property
    def is_foreign_key(self) -> bool:
        return bool(self.foreign_keys)


@dataclass
class RelationMeta:
    """Metadata for a single SQLAlchemy relationship."""

    name: str
    direction: str  # MANYTOONE, ONETOMANY, MANYTOMANY
    target_model: type
    uselist: bool = True
    back_populates: str | None = None
    secondary: Any = None  # association table for many-to-many


@dataclass
class FieldMeta:
    """Metadata for a form field — drives widget rendering and validation."""

    name: str
    label: str
    required: bool
    readonly: bool = False
    help_text: str | None = None
    placeholder: str | None = None
    extra: dict = field(default_factory=dict)


@dataclass
class PermissionSet:
    """Set of boolean permissions for a single model."""

    can_view: bool = False
    can_create: bool = False
    can_edit: bool = False
    can_delete: bool = False


@dataclass
class FieldsetSpec:
    """Defines a logical grouping of fields within a form."""

    title: str | None = None
    collapsed: bool = False
    fields: list[str] = field(default_factory=list)


@dataclass
class SeedRole:
    """Defines a role to be seeded on first startup."""

    name: str
    description: str = ""
    permissions: dict[str, dict[str, bool]] = field(default_factory=dict)
