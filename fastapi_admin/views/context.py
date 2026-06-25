"""ViewContextBuilder — builds template contexts for CRUD views."""

from __future__ import annotations

import math
from typing import Any

from fastapi import Request
from sqlalchemy import and_, asc, desc, func, or_, select
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


class ViewContextBuilder:
    """Builds template contexts for list, form, and delete views.

    Centralizes context construction logic that was previously duplicated
    across multiple factory functions.
    """

    def __init__(
        self,
        registry: Any = None,
        permission_checker: Any = None,
        widget_resolver: Any = None,
    ):
        self.registry = registry
        self.permission_checker = permission_checker
        self.widget_resolver = widget_resolver

    def _get_eager_loads(self, model: Any, list_display: list[str]) -> list:
        """Build eager load options for relationship columns."""
        from sqlalchemy import inspect as sa_inspect

        mapper = sa_inspect(model)
        rel_names = {r.key for r in mapper.relationships}
        options = []
        for col_name in list_display:
            if col_name in rel_names:
                options.append(joinedload(getattr(model, col_name)))
        return options

    def _get_field_type(self, model: Any, field_name: str) -> str:
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
        self, model: Any, field_name: str, session: Any = None
    ) -> dict[str, Any]:
        """Get filter field type and available choices for a field."""
        from sqlalchemy import inspect as sa_inspect
        from sqlalchemy import select as sa_select

        mapper = sa_inspect(model)
        field_type = self._get_field_type(model, field_name)

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
                    q = sa_select(target_model).order_by(target_model).limit(100)
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

    async def build_list_context(
        self,
        registered: RegisteredModel,
        request: Request,
        q: str = "",
        page: int = 1,
        permission_checker: Any = None,
    ) -> dict[str, Any]:
        """Build the template context for a list view.

        Returns a dict suitable for passing to TemplateResponse.
        """
        session = request.app.state.admin_db_session
        model = registered.model
        base = select(model)

        list_display = registered.admin.list_display or [
            c.name for c in registered.columns if c.name != "id"
        ]

        eager_loads = self._get_eager_loads(model, list_display)
        for opt in eager_loads:
            base = base.options(opt)

        active_filters: dict[str, str] = {}
        if registered.admin.list_filter:
            filter_clauses = []
            for filter_field in registered.admin.list_filter:
                param_key = f"filter_{filter_field}"
                filter_value = request.query_params.get(param_key, "")
                if filter_value and hasattr(model, filter_field):
                    field_type = self._get_field_type(model, filter_field)
                    col = getattr(model, filter_field)

                    if field_type == "boolean":
                        bool_val = filter_value == "1"
                        filter_clauses.append(col == bool_val)
                    elif field_type == "datetime":
                        from datetime import datetime as _dt

                        try:
                            parsed = _dt.fromisoformat(filter_value)
                        except (ValueError, TypeError):
                            parsed = None
                        if parsed is not None:
                            filter_clauses.append(col == parsed)
                    elif field_type == "date":
                        from datetime import date as _date

                        try:
                            parsed = _date.fromisoformat(filter_value)
                        except (ValueError, TypeError):
                            parsed = None
                        if parsed is not None:
                            filter_clauses.append(col == parsed)
                    elif field_type == "time":
                        from datetime import time as _time

                        try:
                            parsed = _time.fromisoformat(filter_value)
                        except (ValueError, TypeError):
                            parsed = None
                        if parsed is not None:
                            filter_clauses.append(col == parsed)
                    else:
                        filter_clauses.append(col == filter_value)

                if filter_value:
                    active_filters[filter_field] = filter_value
            if filter_clauses:
                base = base.where(and_(*filter_clauses))

        if q and registered.admin.search_fields:
            clauses = []
            for sf in registered.admin.search_fields:
                if hasattr(model, sf):
                    col = getattr(model, sf)
                    if hasattr(col, "ilike"):
                        clauses.append(col.ilike(f"%{q}%"))
            if clauses:
                base = base.where(or_(*clauses))

        count_q = select(func.count()).select_from(base.subquery())
        total = (await session.execute(count_q)).scalar() or 0

        order = registered.admin.ordering or []
        if order:
            col_name = order[0].lstrip("-")
            col = getattr(model, col_name, None) if hasattr(model, col_name) else None
            if col is not None:
                base = base.order_by(desc(col) if order[0].startswith("-") else asc(col))

        per_page = registered.admin.per_page
        total_pages = max(1, math.ceil(total / per_page))
        page = max(1, min(page, total_pages))
        offset = (page - 1) * per_page
        base = base.offset(offset).limit(per_page)
        result = await session.execute(base)
        items = list(result.unique().scalars().all())

        from sqlalchemy import inspect as sa_inspect
        mapper = sa_inspect(model)
        rel_names = {r.key for r in mapper.relationships}

        display_columns = []
        for col_name in list_display:
            label = col_name.replace("_", " ").title()
            display_columns.append(DisplayColumn(col_name, label, col_name in rel_names))

        filter_fields: dict[str, dict[str, Any]] = {}
        if registered.admin.list_filter:
            for filter_field in registered.admin.list_filter:
                filter_fields[filter_field] = self._get_filter_choices(
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
            "per_page": per_page,
            "filter_fields": filter_fields,
            "active_filters": active_filters,
            "permissions": permission_checker.permission_set(registered.table_name)
            if permission_checker
            else PermissionSet(can_view=True, can_create=True, can_edit=True, can_delete=True),
        }
        inject_sidebar_context(request, template_context)
        return template_context

    def build_form_context(
        self,
        registered: RegisteredModel,
        request: Request,
        obj: Any | None = None,
        values: dict[str, Any] | None = None,
        errors: dict[str, list[str]] | None = None,
        is_create: bool = False,
        permission_checker: Any = None,
    ) -> dict[str, Any]:
        """Build the template context for a form view.

        Returns a dict suitable for passing to TemplateResponse.
        """
        from fastapi_admin.form.pipeline import build_form_context as _build_form_ctx

        ctx = _build_form_ctx(
            registered,
            obj=obj,
            values=values,
            errors=errors,
            request=request,
            is_create=is_create,
        )
        template_context = {
            "form_context": ctx,
            "is_create": is_create,
            "permissions": permission_checker.permission_set(registered.table_name)
            if permission_checker
            else PermissionSet(can_view=True, can_create=True, can_edit=True, can_delete=True),
        }
        inject_sidebar_context(request, template_context)
        return template_context

    def build_delete_context(
        self,
        registered: RegisteredModel,
        request: Request,
        permission_checker: Any = None,
    ) -> dict[str, Any]:
        """Build the template context for a delete confirmation view.

        Returns a dict suitable for passing to TemplateResponse.
        """
        template_context = {
            "model": registered,
            "registered": registered,
            "permissions": permission_checker.permission_set(registered.table_name)
            if permission_checker
            else PermissionSet(can_view=True, can_create=True, can_edit=True, can_delete=True),
        }
        inject_sidebar_context(request, template_context)
        return template_context
