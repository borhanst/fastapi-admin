"""List view handler factory for registered models."""

from __future__ import annotations

from typing import Any

from fastapi_admin.registry import RegisteredModel
from fastapi_admin.views.context import ViewContextBuilder


def _get_eager_loads(model: Any, list_display: list[str]) -> list:
    """Build eager load options for relationship columns."""
    from sqlalchemy import inspect as sa_inspect
    from sqlalchemy.orm import joinedload

    mapper = sa_inspect(model)
    rel_names = {r.key for r in mapper.relationships}
    options = []
    for col_name in list_display:
        if col_name in rel_names:
            options.append(joinedload(getattr(model, col_name)))
    return options


def _get_field_type(model: Any, field_name: str) -> str:
    """Detect the abstract field type for a model field."""
    from sqlalchemy import inspect as sa_inspect

    mapper = sa_inspect(model)
    rel_names = {r.key for r in mapper.relationships}

    if field_name in rel_names:
        return "relation"

    for prop in mapper.column_attrs:
        if prop.key == field_name:
            col = prop.columns[0] if prop.columns else None
            if col is None:
                break
            type_name = col.type.__class__.__name__
            if type_name == "Boolean":
                return "boolean"
            if type_name == "DateTime":
                return "datetime"
            if type_name == "Date":
                return "date"
            if type_name == "Time":
                return "time"
            if hasattr(col.type, "enums") and col.type.enums:
                return "enum"
            if col.foreign_keys:
                return "relation"
            return "text"
    return "text"


def _get_filter_choices(
    model: Any, field_name: str, session: Any = None
) -> dict[str, Any]:
    """Get filter field type and available choices for a field."""
    from sqlalchemy import inspect as sa_inspect
    from sqlalchemy import select

    mapper = sa_inspect(model)
    field_type = _get_field_type(model, field_name)

    if field_type == "relation":
        rel_map = {r.key: r for r in mapper.relationships}
        target_model = None
        if field_name in rel_map:
            target_model = rel_map[field_name].mapper.class_
        else:
            for rel in mapper.relationships:
                if rel.direction.name == "MANYTOONE":
                    for prop in mapper.column_attrs:
                        if prop.key == field_name:
                            col = prop.columns[0] if prop.columns else None
                            if col is not None:
                                for fk in col.foreign_keys:
                                    if fk.column.table == rel.mapper.persist_selectable:
                                        target_model = rel.mapper.class_
                                        break
                    if target_model is not None:
                        break

        choices: list[tuple[str, str]] = [("", "All")]
        if target_model is not None and session is not None:
            try:
                q = select(target_model).order_by(target_model).limit(100)
                result = session.execute(q)
                for obj in result.scalars():
                    choices.append((str(obj.id), str(obj)))
            except Exception:
                pass
        return {"field_type": field_type, "choices": choices}

    if field_type == "boolean":
        return {
            "field_type": "boolean",
            "choices": [("", "All"), ("1", "Yes"), ("0", "No")],
        }

    if field_type == "enum":
        for prop in mapper.column_attrs:
            if prop.key == field_name:
                col = prop.columns[0] if prop.columns else None
                if col is not None and hasattr(col.type, "enums"):
                    choices = [("", "All")]
                    for val in col.type.enums:
                        choices.append((val, val.replace("_", " ").title()))
                    return {"field_type": "enum", "choices": choices}

    if field_type in ("date", "datetime", "time"):
        return {"field_type": field_type, "choices": [("", "All")]}

    choices = [("", "All")]
    for prop in mapper.column_attrs:
        if prop.key == field_name:
            col = prop.columns[0] if prop.columns else None
            if col is not None and session is not None:
                try:
                    q = (
                        select(col)
                        .where(col.isnot(None))
                        .group_by(col)
                        .order_by(col)
                        .limit(100)
                    )
                    result = session.execute(q)
                    for (val,) in result:
                        label = str(val).replace("_", " ").title()
                        choices.append((str(val), label))
                except Exception:
                    pass
    return {"field_type": "text", "choices": choices}


def list_view_factory(registered: RegisteredModel):
    """Create a list view handler using ViewFactory internally.

    This function maintains backward compatibility while delegating
    to the new ViewContextBuilder for context construction.
    """
    from fastapi_admin.views.factory import ViewFactory

    factory = ViewFactory(context_builder=ViewContextBuilder())
    return factory.create_list_view(registered)
