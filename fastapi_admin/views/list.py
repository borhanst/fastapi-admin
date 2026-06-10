"""List view handler factory for registered models."""

from __future__ import annotations

import math
from typing import Any

from fastapi import Request
from sqlalchemy import desc, asc, select, func, or_
from sqlalchemy.orm import joinedload
from fastapi_admin.registry import RegisteredModel
from fastapi_admin.types import PermissionSet


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

        return templates.TemplateResponse(request, "pages/list.html", {
            "model": registered,
            "display_columns": display_columns,
            "items": items,
            "search_query": q,
            "page": page,
            "total_pages": total_pages,
            "total": total,
            "permissions": PermissionSet(
                can_view=True,
                can_create=True,
                can_edit=True,
                can_delete=True,
            ),
        })
    list_view.__name__ = f"list_{registered.table_name}"
    return list_view
