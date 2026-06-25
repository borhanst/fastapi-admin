"""List view handler factory for registered models.

Backward-compatible wrapper — delegates to ListView class.
"""

from __future__ import annotations

from typing import Any

<<<<<<< HEAD:fastapi_console/views/list.py
from fastapi import Request
from sqlalchemy import and_, asc, desc, func, or_, select
from sqlalchemy.orm import joinedload

from fastapi_console.registry import RegisteredModel
from fastapi_console.types import PermissionSet
from fastapi_console.views.sidebar import inject_sidebar_context


class DisplayColumn:
    """Helper to render a column in the list view."""

    def __init__(self, name: str, label: str, is_relation: bool = False):
        self.name = name
        self.label = label
        self.is_relation = is_relation

    def value(self, obj: Any) -> Any:
        return getattr(obj, self.name, "")


def _get_eager_loads(model: Any, list_display: list[str]) -> list:
    """Build eager load options for relationship columns."""
    from sqlalchemy import inspect as sa_inspect

    mapper = sa_inspect(model)
    rel_names = {r.key for r in mapper.relationships}
    options = []
    for col_name in list_display:
        if col_name in rel_names:
            options.append(joinedload(getattr(model, col_name)))
    return options


def _get_field_type(model: Any, field_name: str) -> str:
    """Detect the abstract field type for a model field.

    Returns one of: "boolean", "datetime", "date", "time", "enum",
    "relation", "text".
    """
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
    """Get filter field type and available choices for a field.

    Returns ``{"field_type": str, "choices": [(value, label), ...]}``.
    """
    from sqlalchemy import inspect as sa_inspect
    from sqlalchemy import select

    mapper = sa_inspect(model)
    field_type = _get_field_type(model, field_name)

    # Relationship field — query related model objects
    if field_type == "relation":
        rel_map = {r.key: r for r in mapper.relationships}
        target_model = None
        if field_name in rel_map:
            target_model = rel_map[field_name].mapper.class_
        else:
            # FK column name (e.g. "category_id") — find matching relationship
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

    # Boolean
    if field_type == "boolean":
        return {
            "field_type": "boolean",
            "choices": [("", "All"), ("1", "Yes"), ("0", "No")],
        }

    # Enum
    if field_type == "enum":
        for prop in mapper.column_attrs:
            if prop.key == field_name:
                col = prop.columns[0] if prop.columns else None
                if col is not None and hasattr(col.type, "enums"):
                    choices = [("", "All")]
                    for val in col.type.enums:
                        choices.append((val, val.replace("_", " ").title()))
                    return {"field_type": "enum", "choices": choices}

    # Date / DateTime / Time — no choices, rendered as input
    if field_type in ("date", "datetime", "time"):
        return {"field_type": field_type, "choices": [("", "All")]}

    # Text / other — query distinct values
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
=======
from fastapi_admin.registry import RegisteredModel
>>>>>>> 6fbbaad1ffffd156930439440a97eefaf7f5c603:fastapi_admin/views/list.py


def list_view_factory(registered: RegisteredModel):
    """Create a list view handler — delegates to ListView.html_response."""
    from fastapi_admin.views.class_views import ListView, _resolve_view_class

    view_class = _resolve_view_class(registered.admin, "list_view_class", ListView)
    view_instance = view_class(registered)

    async def _handler(request: Request, **kwargs: Any):
        return await view_instance.html_response(request, **kwargs)

    _handler.__name__ = f"list_{registered.table_name}"
    return _handler


# Need Request for type annotation in the wrapper
from fastapi import Request  # noqa: E402
