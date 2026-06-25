"""WidgetRegistry — stores type-to-widget and name-to-widget mappings.

This class handles ONLY registration/storage of widget mappings.
Resolution logic lives in WidgetResolver (fastapi_admin/widgets/resolver.py).

Resolution order (documented here for reference, implemented in WidgetResolver):
  1. Exact field name pattern  ->  e.g. "password" -> PasswordWidget
  2. FK column present         ->  RelationPickerWidget
  3. Enum type                 ->  SelectWidget
  4. SQLAlchemy type match     ->  via type_map dict
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
    Uuid,
)

<<<<<<< HEAD:fastapi_console/widgets/registry.py
from fastapi_console.types import ColumnMeta
from fastapi_console.widgets.base import Widget
from fastapi_console.widgets.inputs import (
=======
from fastapi_admin.widgets.base import Widget
from fastapi_admin.widgets.inputs import (
>>>>>>> 6fbbaad1ffffd156930439440a97eefaf7f5c603:fastapi_admin/widgets/registry.py
    DatePickerWidget,
    DateTimePickerWidget,
    FileUploadWidget,
    NumberInputWidget,
    PasswordWidget,
    TextareaWidget,
    TextInputWidget,
    ToggleWidget,
)


class WidgetRegistry:
    """Stores SQLAlchemy column type and name pattern mappings to widget classes.

    This class is responsible ONLY for registration and storage.
    Use WidgetResolver to determine which widget to use for a column.
    """

    def __init__(self) -> None:
        self._type_map: dict[type, type[Widget]] = {}
        self._name_patterns: list[tuple[str, type[Widget]]] = []

    @property
    def type_map(self) -> dict[type, type[Widget]]:
        """Read-only access to the type-to-widget mapping."""
        return dict(self._type_map)

    @property
    def name_patterns(self) -> list[tuple[str, type[Widget]]]:
        """Read-only access to the name pattern list."""
        return list(self._name_patterns)

    def register_type(self, sa_type: type, widget_cls: type[Widget]) -> None:
        """Register a widget class for a SQLAlchemy column type."""
        self._type_map[sa_type] = widget_cls

    def unregister_type(self, sa_type: type) -> None:
        """Remove a registered type mapping."""
        self._type_map.pop(sa_type, None)

    def register_name(self, pattern: str, widget_cls: type[Widget]) -> None:
        """Register a widget class for a name pattern (case-insensitive substring)."""
        self._name_patterns.append((pattern.lower(), widget_cls))

    def unregister_name(self, pattern: str) -> None:
        """Remove all registrations for a name pattern."""
        self._name_patterns = [
            (p, w) for p, w in self._name_patterns if p != pattern.lower()
        ]

<<<<<<< HEAD:fastapi_console/widgets/registry.py
        if col.foreign_keys:
            from fastapi_console.widgets.relation import RelationPickerWidget
=======
    def clear(self) -> None:
        """Remove all registered mappings."""
        self._type_map.clear()
        self._name_patterns.clear()
>>>>>>> 6fbbaad1ffffd156930439440a97eefaf7f5c603:fastapi_admin/widgets/registry.py

    def has_type(self, sa_type: type) -> bool:
        """Check if a type is registered."""
        return sa_type in self._type_map

<<<<<<< HEAD:fastapi_console/widgets/registry.py
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
=======
    def has_name(self, pattern: str) -> bool:
        """Check if a name pattern is registered."""
        return any(p == pattern.lower() for p, _ in self._name_patterns)
>>>>>>> 6fbbaad1ffffd156930439440a97eefaf7f5c603:fastapi_admin/widgets/registry.py


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
