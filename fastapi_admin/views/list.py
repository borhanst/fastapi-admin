"""List view handler factory for registered models."""

from __future__ import annotations

import math
from typing import Any

from fastapi import Request
from sqlalchemy import desc, asc, select, func, or_, and_
from sqlalchemy.orm import joinedload
from fastapi_admin.registry import RegisteredModel
from fastapi_admin.types import PermissionSet
from fastapi_admin.views.sidebar import inject_sidebar_context


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


def _get_filter_choices(
    model: Any, field_name: str, session: Any = None
) -> list[tuple[str, str]]:
    """Get available filter choices for a field. Returns list of (value, label)."""
    from sqlalchemy import inspect as sa_inspect, select, func

    choices: list[tuple[str, str]] = [("", "All")]
    mapper = sa_inspect(model)
    for prop in mapper.column_attrs:
        if prop.key == field_name:
            col = prop.columns[0] if prop.columns else None
            if col is not None:
                # Boolean field
                if col.type.__class__.__name__ == "Boolean":
                    choices.append(("1", "Yes"))
                    choices.append(("0", "No"))
                # Enum field
                elif hasattr(col.type, "enums") and col.type.enums:
                    for val in col.type.enums:
                        choices.append((val, val.replace("_", " ").title()))
                # String/other fields — query distinct values
                elif session is not None:
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
    return choices


def list_view_factory(registered: RegisteredModel):
    async def list_view(request: Request, q: str = "", page: int = 1, _: Any = None):
        templates = request.app.state.admin_jinja_env
        session = request.app.state.admin_db_session
        model = registered.model
        base = select(model)

        # Build display columns from list_display
        list_display = registered.admin.list_display or [
            c.name for c in registered.columns if c.name != "id"
        ]

        # Eagerly load relationships to avoid lazy-load in async context
        eager_loads = _get_eager_loads(model, list_display)
        for opt in eager_loads:
            base = base.options(opt)

        # Apply list_filter
        active_filters: dict[str, str] = {}
        if registered.admin.list_filter:
            filter_clauses = []
            for filter_field in registered.admin.list_filter:
                param_key = f"filter_{filter_field}"
                filter_value = request.query_params.get(param_key, "")
                if filter_value and hasattr(model, filter_field):
                    col = getattr(model, filter_field)
                    # Boolean filter
                    if filter_value in ("0", "1"):
                        bool_val = filter_value == "1"
                        filter_clauses.append(col == bool_val)
                    else:
                        filter_clauses.append(col == filter_value)
                if filter_value:
                    active_filters[filter_field] = filter_value
            if filter_clauses:
                base = base.where(and_(*filter_clauses))

        # Search
        if q and registered.admin.search_fields:
            clauses = []
            for sf in registered.admin.search_fields:
                if hasattr(model, sf):
                    col = getattr(model, sf)
                    if hasattr(col, "ilike"):
                        clauses.append(col.ilike(f"%{q}%"))
            if clauses:
                base = base.where(or_(*clauses))

        # Count total
        count_q = select(func.count()).select_from(base.subquery())
        total = (await session.execute(count_q)).scalar() or 0

        # Ordering
        order = registered.admin.ordering or []
        if order:
            col_name = order[0].lstrip("-")
            col = getattr(model, col_name, None) if hasattr(model, col_name) else None
            if col is not None:
                base = base.order_by(desc(col) if order[0].startswith("-") else asc(col))

        # Pagination
        per_page = registered.admin.per_page
        total_pages = max(1, math.ceil(total / per_page))
        page = max(1, min(page, total_pages))
        offset = (page - 1) * per_page
        base = base.offset(offset).limit(per_page)
        result = await session.execute(base)
        # Deduplicate due to joinedload producing duplicate rows
        items = list(result.unique().scalars().all())

        # Detect relation columns
        from sqlalchemy import inspect as sa_inspect
        mapper = sa_inspect(model)
        rel_names = {r.key for r in mapper.relationships}

        display_columns = []
        for col_name in list_display:
            label = col_name.replace("_", " ").title()
            display_columns.append(DisplayColumn(col_name, label, col_name in rel_names))

        # Build filter choices for template
        filter_fields: dict[str, list[tuple[str, str]]] = {}
        if registered.admin.list_filter:
            for filter_field in registered.admin.list_filter:
                filter_fields[filter_field] = _get_filter_choices(
                    model, filter_field, session
                )

        template_context = {
            "model": registered,
            "registered": registered,
            "display_columns": display_columns,
            "items": items,
            "search_query": q,
            "page": page,
            "total_pages": total_pages,
            "total": total,
            "filter_fields": filter_fields,
            "active_filters": active_filters,
            "permissions": PermissionSet(
                can_view=True,
                can_create=True,
                can_edit=True,
                can_delete=True,
            ),
        }
        inject_sidebar_context(request, template_context)

        return templates.TemplateResponse(request, "pages/list.html", template_context)
    list_view.__name__ = f"list_{registered.table_name}"
    return list_view
