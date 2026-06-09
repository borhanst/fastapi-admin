"""WidgetRegistry — resolves which widget to use for a given ColumnMeta.

Resolution order (fixed, cannot be short-circuited):
  1. Exact field name pattern  →  e.g. "password" → PasswordWidget
  2. FK column present         →  RelationPickerWidget
  3. Enum type                 →  SelectWidget
  4. SQLAlchemy type match     →  via _type_map dict
  5. Fallback                  →  TextInputWidget
"""

from __future__ import annotations

from fastapi_admin.types import ColumnMeta
from fastapi_admin.widgets.base import Widget
from fastapi_admin.widgets.inputs import TextInputWidget


class WidgetRegistry:
    """Maps SQLAlchemy column types and name patterns to widget classes."""

    def __init__(self) -> None:
        self._type_map: dict[type, type[Widget]] = {}
        self._name_patterns: list[tuple[str, type[Widget]]] = []

    def register_type(self, sa_type: type, widget_cls: type[Widget]) -> None:
        """Register a widget class for a SQLAlchemy column type."""
        self._type_map[sa_type] = widget_cls

    def register_name(self, pattern: str, widget_cls: type[Widget]) -> None:
        """Register a widget class for a name pattern (case-insensitive substring)."""
        self._name_patterns.append((pattern.lower(), widget_cls))

    def resolve(self, col: ColumnMeta) -> Widget:
        """Resolve which widget instance to use for a given column."""
        # 1. Name patterns
        for pattern, widget_cls in self._name_patterns:
            if pattern in col.name.lower():
                return widget_cls()

        # 2. FK
        if col.foreign_keys:
            from fastapi_admin.widgets.relation import RelationPickerWidget

            return RelationPickerWidget()

        # 3. Enum — check for Python enum.Enum type or SQLAlchemy Enum
        col_type = col.type
        if hasattr(col_type, "enums") and col_type.enums:
            choices = [(v, v.replace("_", " ").title()) for v in col_type.enums]
            from fastapi_admin.widgets.inputs import SelectWidget

            return SelectWidget(choices=choices)

        # 4. Type hierarchy
        for sa_type, widget_cls in self._type_map.items():
            if isinstance(col_type, sa_type):
                has_length = hasattr(col_type, "length") and col_type.length
                if widget_cls == TextInputWidget and has_length:
                    return TextInputWidget(maxlength=col_type.length)
                return widget_cls()

        # 5. Fallback
        return TextInputWidget()
