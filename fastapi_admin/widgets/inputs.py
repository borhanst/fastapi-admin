"""Built-in widget classes — all standard form widgets per spec."""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any

from fastapi_admin.types import FieldMeta
from fastapi_admin.widgets.base import Widget


class TextInputWidget(Widget):
    macro_name = "text_input"

    def __init__(self, maxlength: int | None = None):
        self.maxlength = maxlength

    def render_context(self, field: FieldMeta, value: Any) -> dict:
        ctx = super().render_context(field, value)
        ctx["maxlength"] = self.maxlength
        return ctx

    def validate(self, value: Any, field: FieldMeta) -> list[str]:
        errors = super().validate(value, field)
        if value and self.maxlength and len(value) > self.maxlength:
            errors.append(f"{field.label} must be {self.maxlength} characters or fewer.")
        return errors


class TextareaWidget(Widget):
    macro_name = "textarea"

    def __init__(self, rows: int = 5):
        self.rows = rows

    def render_context(self, field: FieldMeta, value: Any) -> dict:
        ctx = super().render_context(field, value)
        ctx["rows"] = self.rows
        return ctx


class NumberInputWidget(Widget):
    macro_name = "number_input"

    def __init__(self, step: str = "1", min: str | None = None, max: str | None = None):
        self.step = step
        self.min = min
        self.max = max

    def render_context(self, field: FieldMeta, value: Any) -> dict:
        ctx = super().render_context(field, value)
        ctx.update({"step": self.step, "min": self.min, "max": self.max})
        return ctx

    def parse(self, raw: str | None) -> int | float | None:
        if raw is None or raw == "":
            return None
        try:
            return int(raw) if "." not in str(raw) else float(raw)
        except ValueError:
            return raw

    def validate(self, value: Any, field: FieldMeta) -> list[str]:
        errors = super().validate(value, field)
        if value is not None:
            try:
                float(value)
            except (TypeError, ValueError):
                errors.append(f"{field.label} must be a number.")
        return errors


class ToggleWidget(Widget):
    macro_name = "toggle"

    def parse(self, raw: str | None) -> bool:
        if raw is None:
            return False
        if isinstance(raw, bool):
            return raw
        return str(raw).lower() in ("on", "true", "1", "yes")

    def validate(self, value: Any, field: FieldMeta) -> list[str]:
        return []


class SelectWidget(Widget):
    macro_name = "select"

    def __init__(self, choices: list[tuple[str, str]] | None = None):
        self.choices = choices or []

    def render_context(self, field: FieldMeta, value: Any) -> dict:
        ctx = super().render_context(field, value)
        ctx["choices"] = self.choices
        return ctx

    def validate(self, value: Any, field: FieldMeta) -> list[str]:
        errors = super().validate(value, field)
        if value and self.choices:
            valid = {c[0] for c in self.choices}
            if value not in valid:
                errors.append(f"'{value}' is not a valid choice for {field.label}.")
        return errors


class DatePickerWidget(Widget):
    macro_name = "date_picker"

    def parse(self, raw: str | None) -> date | str | None:
        if not raw:
            return None
        try:
            return date.fromisoformat(raw)
        except ValueError:
            return raw

    def validate(self, value: Any, field: FieldMeta) -> list[str]:
        errors = super().validate(value, field)
        if value is not None and not isinstance(value, date):
            errors.append(f"{field.label} must be a valid date.")
        return errors


class DateTimePickerWidget(Widget):
    macro_name = "datetime_picker"

    def parse(self, raw: str | None) -> datetime | str | None:
        if not raw:
            return None
        try:
            return datetime.fromisoformat(raw)
        except ValueError:
            return raw

    def validate(self, value: Any, field: FieldMeta) -> list[str]:
        errors = super().validate(value, field)
        if value is not None and not isinstance(value, datetime):
            errors.append(f"{field.label} must be a valid date and time.")
        return errors


class JsonEditorWidget(Widget):
    macro_name = "json_editor"

    def parse(self, raw: str | None) -> Any:
        if not raw:
            return None
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                return None
        return raw

    def validate(self, value: Any, field: FieldMeta) -> list[str]:
        errors = super().validate(value, field)
        if isinstance(value, str):
            try:
                json.loads(value)
            except json.JSONDecodeError as e:
                errors.append(f"{field.label} contains invalid JSON: {e}")
        return errors


class PasswordWidget(Widget):
    macro_name = "password_input"

    def render_context(self, field: FieldMeta, value: Any) -> dict:
        ctx = super().render_context(field, value)
        ctx["value"] = ""  # NEVER pre-fill passwords
        return ctx

    def parse(self, raw: str | None) -> str | None:
        if not raw:
            return None
        return raw


class ReadOnlyWidget(Widget):
    macro_name = "readonly"

    def parse(self, raw: str | None) -> None:
        return None

    def validate(self, value: Any, field: FieldMeta) -> list[str]:
        return []


class HiddenWidget(Widget):
    macro_name = "hidden"
