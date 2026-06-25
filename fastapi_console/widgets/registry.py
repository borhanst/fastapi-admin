"""WidgetRegistry — resolves which widget to use for a given ColumnMeta.

Resolution order (fixed, cannot be short-circuited):
  1. Exact field name pattern  ->  e.g. "password" -> PasswordWidget
  2. FK column present         ->  RelationPickerWidget
  3. Enum type                 ->  SelectWidget
  4. SQLAlchemy type match     ->  via _type_map dict
  5. Fallback                  ->  TextInputWidget
"""

from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
    Time,
    Uuid,
)

from fastapi_console.types import ColumnMeta
from fastapi_console.widgets.base import Widget
from fastapi_console.widgets.inputs import (
    DatePickerWidget,
    DateTimePickerWidget,
    FileUploadWidget,
    JsonEditorWidget,
    NumberInputWidget,
    PasswordWidget,
    TextInputWidget,
    TextareaWidget,
    ToggleWidget,
)


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
        for pattern, widget_cls in self._name_patterns:
            if pattern in col.name.lower():
                return widget_cls()

        if col.foreign_keys:
            from fastapi_console.widgets.relation import RelationPickerWidget

            return RelationPickerWidget()

        col_type = col.type
        if hasattr(col_type, "enums") and col_type.enums:
            choices = [(v, v.replace("_", " ").title()) for v in col_type.enums]
            from fastapi_console.widgets.inputs import SelectWidget

            return SelectWidget(choices=choices)

        for sa_type, widget_cls in self._type_map.items():
            if isinstance(col_type, sa_type):
                has_length = hasattr(col_type, "length") and col_type.length
                if widget_cls == TextInputWidget and has_length:
                    return TextInputWidget(maxlength=col_type.length)
                return widget_cls()

        return TextInputWidget()


widget_registry = WidgetRegistry()

widget_registry.register_type(String, TextInputWidget)
widget_registry.register_type(Text, TextareaWidget)
widget_registry.register_type(Integer, NumberInputWidget)
widget_registry.register_type(Float, NumberInputWidget)
widget_registry.register_type(Numeric, NumberInputWidget)
widget_registry.register_type(Boolean, ToggleWidget)
widget_registry.register_type(Date, DatePickerWidget)
widget_registry.register_type(DateTime, DateTimePickerWidget)
widget_registry.register_type(LargeBinary, FileUploadWidget)
widget_registry.register_type(Uuid, TextInputWidget)

widget_registry.register_name("password", PasswordWidget)
widget_registry.register_name("secret", PasswordWidget)
widget_registry.register_name("token", PasswordWidget)
