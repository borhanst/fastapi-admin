"""ModelInspector — inspects SQLAlchemy models and extracts metadata."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from sqlalchemy import inspect

from fastapi_admin.types import ColumnMeta, RelationMeta

if TYPE_CHECKING:
    pass


class ModelInspector:
    """Inspects SQLAlchemy models and extracts column/relationship metadata.

    This class centralizes all model inspection logic, making it testable
    and separable from the registry's storage concerns.
    """

    def inspect_model(
        self, model: type
    ) -> tuple[list[ColumnMeta], list[RelationMeta]]:
        """Inspect a SQLAlchemy model and return column + relationship metadata.

        Args:
            model: A SQLAlchemy declarative model class.

        Returns:
            A tuple of (columns, relationships) metadata.
        """
        mapper = inspect(model)
        columns: list[ColumnMeta] = []
        relationships: list[RelationMeta] = []

        for col in mapper.columns:
            columns.append(
                ColumnMeta(
                    name=col.key,
                    type=col.type,
                    nullable=col.nullable,
                    primary_key=col.primary_key,
                    foreign_keys=list(col.foreign_keys),
                    default=col.default,
                    server_default=col.server_default,
                    index=col.index,
                    unique=col.unique,
                )
            )

        for rel in mapper.relationships:
            relationships.append(
                RelationMeta(
                    name=rel.key,
                    direction=rel.direction.name,
                    target_model=rel.mapper.class_,
                    uselist=rel.uselist,
                    back_populates=rel.back_populates,
                    secondary=rel.secondary,
                )
            )

        return columns, relationships

    def validate_model(self, model: type) -> None:
        """Validate that a model is suitable for admin registration.

        Args:
            model: A SQLAlchemy declarative model class.

        Raises:
            ValueError: If the model is not a valid SQLAlchemy model.
        """
        if not hasattr(model, "__tablename__"):
            raise ValueError(
                f"{model.__name__} is not a SQLAlchemy model (no __tablename__)"
            )

    def extract_metadata(
        self,
        model: type,
        columns: list[ColumnMeta],
        relationships: list[RelationMeta],
    ) -> dict[str, Any]:
        """Extract additional metadata from a model.

        Args:
            model: A SQLAlchemy declarative model class.
            columns: The extracted column metadata.
            relationships: The extracted relationship metadata.

        Returns:
            A dictionary of extracted metadata.
        """
        pk_field = self.get_pk_field(model)
        table_name = model.__tablename__

        return {
            "table_name": table_name,
            "pk_field": pk_field,
            "columns": columns,
            "relationships": relationships,
        }

    def is_abstract(self, model: type) -> bool:
        """Check if a model is abstract and should be skipped during auto-discovery.

        Args:
            model: A SQLAlchemy declarative model class.

        Returns:
            True if the model is abstract, False otherwise.
        """
        return getattr(model, "__abstract__", False)

    def get_pk_field(self, model: type) -> str | tuple[str, ...] | None:
        """Get the primary key field name for a model.

        Args:
            model: A SQLAlchemy declarative model class.

        Returns:
            The single PK field name for simple PKs,
            a tuple of names for composite PKs,
            or None if no primary key is found.
        """
        mapper = inspect(model)
        pk_cols = mapper.primary_key
        if not pk_cols:
            return None
        if len(pk_cols) == 1:
            return pk_cols[0].key
        return tuple(col.key for col in pk_cols)

    def auto_label(self, name: str) -> str:
        """Auto-generate a human-readable label from a field name.

        Args:
            name: The field name to convert.

        Returns:
            A human-readable label.

        Examples:
            "category_id"  → "Category"
            "is_active"    → "Is Active"
            "created_at"   → "Created At"
            "skuCode"      → "Sku Code"
        """
        label = name
        if label.endswith("_id"):
            label = label[:-3]
        label = re.sub(r"([A-Z])", r" \1", label)
        return label.replace("_", " ").strip().title()

    def is_required(self, col: ColumnMeta) -> bool:
        """Determine if a column is required (NOT NULL with no default).

        A column is required if:
        - It is NOT NULL
        - It has no Python default
        - It has no server_default (DB-side default)
        - It is NOT a primary key (PKs are handled separately)

        Args:
            col: The column metadata to check.

        Returns:
            True if the column is required, False otherwise.
        """
        return (
            not col.nullable
            and col.default is None
            and col.server_default is None
            and not col.primary_key
        )
