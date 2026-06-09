"""Relation widgets — ForeignKey and many-to-many pickers."""

from __future__ import annotations

from typing import Any

from fastapi_admin.types import FieldMeta
from fastapi_admin.widgets.base import Widget


class RelationPickerWidget(Widget):
    """ForeignKey (many-to-one) picker — HTMX async searchable select."""

    macro_name = "relation_picker"

    def __init__(self, related_table: str = "", related_verbose: str = ""):
        self.related_table = related_table
        self.related_verbose = related_verbose

    def parse(self, raw: str | None) -> int | str | None:
        if not raw:
            return None
        try:
            return int(raw)
        except ValueError:
            return raw

    def render_context(self, field: FieldMeta, value: Any) -> dict:
        ctx = super().render_context(field, value)
        ctx["related_table"] = self.related_table
        ctx["related_verbose"] = self.related_verbose
        return ctx


class MultiRelationWidget(Widget):
    """Many-to-many tag-style multi-select."""

    macro_name = "multi_relation"

    def parse(self, raw: str | list | None) -> list[str]:
        if raw is None:
            return []
        if isinstance(raw, list):
            return [str(v) for v in raw if v]
        return [str(raw)]

    def validate(self, value: Any, field: FieldMeta) -> list[str]:
        return []
