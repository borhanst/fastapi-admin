"""Widgets module — base class, all built-in widgets, WidgetRegistry."""

from __future__ import annotations

from fastapi_admin.widgets.base import Widget
from fastapi_admin.widgets.inputs import (
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
from fastapi_admin.widgets.registry import WidgetRegistry
from fastapi_admin.widgets.relation import MultiRelationWidget, RelationPickerWidget

__all__ = [
    "Widget",
    "WidgetRegistry",
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
