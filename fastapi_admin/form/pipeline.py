"""Build FormContext from a RegisteredModel + DB object + values + errors."""

from __future__ import annotations

from typing import Any

from fastapi_admin.types import (
    FieldsetContext,
    FieldRenderContext,
    PermissionSet,
    FormContext,
)
from fastapi_admin.widgets.registry import widget_registry
from fastapi_admin.inspection import auto_label, get_pk_field


def build_form_context(
    registered: Any,
    obj: Any | None = None,
    values: dict[str, Any] | None = None,
    errors: dict[str, list[str]] | None = None,
    request: Any = None,
    is_create: bool = False,
    rel_labels: dict[str, str] | None = None,
) -> FormContext:
    values = values or {}
    errors = errors or {}
    rendered: list[FieldRenderContext] = []
    fieldsets: list[FieldsetContext] = [FieldsetContext(fields=[])]

    pk = registered.pk_field if is_create else registered.pk_field

    for field_meta in registered.form_fields:
        col = next((c for c in registered.columns if c.name == field_meta.name), None)
        rel = next((r for r in registered.relationships if r.name == field_meta.name), None)
        widget = registered.get_widget(field_meta.name)

        value = values.get(field_meta.name)
        if value is None and obj is not None:
            if hasattr(obj, "__dict__"):
                value = obj.__dict__.get(field_meta.name)
            # For relationship fields, read the FK column value to avoid lazy load
            if value is None and rel is not None:
                try:
                    from sqlalchemy import inspect as sa_inspect
                    mapper = sa_inspect(type(obj))
                    rel_prop = mapper.relationships.get(rel.name)
                    if rel_prop is not None:
                        local_cols = [c.key for c in rel_prop.local_columns]
                        if local_cols:
                            value = getattr(obj, local_cols[0], None)
                except Exception:
                    pass
            elif value is None and col is not None:
                value = getattr(obj, field_meta.name, None)

        widget_macro = widget.macro_name
        widget_ctx = widget.render_context(field_meta, value)
        if rel is not None and rel_labels:
            widget_ctx["label_text"] = rel_labels.get(rel.name, "")
        field_errors = errors.get(field_meta.name, [])
        rendered.append(
            FieldRenderContext(
                meta=field_meta,
                widget_macro=widget_macro,
                widget_context=widget_ctx,
                errors=field_errors,
            )
        )

    fieldsets[0].fields = rendered

    return FormContext(
        model_name=registered.table_name,
        verbose_name=registered.verbose_name,
        is_create=is_create,
        obj=obj,
        fieldsets=fieldsets,
        errors=errors,
        values=values,
        action_url="",
        list_url="",
        can_delete=not is_create,
        permissions=PermissionSet(),
        readonly=False,
    )
