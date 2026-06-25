"""Widgets module — base class, all built-in widgets, WidgetRegistry, WidgetResolver."""

from __future__ import annotations

from fastapi_console.widgets.base import Widget
from fastapi_console.widgets.inputs import (
    DatePickerWidget,
    DateTimePickerWidget,
    FileUploadWidget,
    HiddenWidget,
    ImageUploadWidget,
    JsonEditorWidget,
    NumberInputWidget,
    PasswordWidget,
    ReadOnlyWidget,
    SelectWidget,
    TextareaWidget,
    TextInputWidget,
    ToggleWidget,
)
<<<<<<< HEAD:fastapi_console/widgets/__init__.py
from fastapi_console.widgets.registry import WidgetRegistry
from fastapi_console.widgets.relation import MultiRelationWidget, RelationPickerWidget
=======
from fastapi_admin.widgets.registry import WidgetRegistry
from fastapi_admin.widgets.relation import MultiRelationWidget, RelationPickerWidget
from fastapi_admin.widgets.resolver import WidgetResolver
>>>>>>> 6fbbaad1ffffd156930439440a97eefaf7f5c603:fastapi_admin/widgets/__init__.py

__all__ = [
    "Widget",
    "WidgetRegistry",
    "WidgetResolver",
    "TextInputWidget",
    "TextareaWidget",
    "NumberInputWidget",
    "ToggleWidget",
    "DatePickerWidget",
    "DateTimePickerWidget",
    "SelectWidget",
    "JsonEditorWidget",
    "PasswordWidget",
    "ReadOnlyWidget",
    "HiddenWidget",
    "FileUploadWidget",
    "ImageUploadWidget",
    "RelationPickerWidget",
    "MultiRelationWidget",
]
