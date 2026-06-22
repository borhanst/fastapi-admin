"""Class-based view orchestrators for CRUD operations.

SRP: Each view class coordinates a single workflow.
OCP: Extend by subclassing, never modify the base.
DIP: Compose via protocol abstractions (renderer, parser, query provider).
"""

from __future__ import annotations

import math
from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse, Response

from fastapi_admin.flash import add_flash
from fastapi_admin.registry import RegisteredModel
from fastapi_admin.views.context import DisplayColumn
from fastapi_admin.views.renderers import (
    DefaultQueryProvider,
    FormHTMLRenderer,
    HTMLFormParser,
    ItemAPIRenderer,
    JSONBodyParser,
    ListAPIRenderer,
    ListHTMLRenderer,
    _resolve_permission_checker,
)


def _resolve_view_class(admin: Any, attr: str, default: type) -> type:
    """Resolve a view class from ModelAdmin, falling back to default."""
    cls = getattr(admin, attr, None)
    return cls if cls is not None else default


class BaseView:
    """Base class — holds registered model, provides dependency injection.

    Subclass and override class attributes to swap implementations (DIP).
    """

    # Class-level defaults — override per-model or subclass (OCP)
    query_provider_class: type = DefaultQueryProvider
    form_parser_class: type = HTMLFormParser
    html_renderer_class: type | None = None
    api_renderer_class: type | None = None

    def __init__(self, registered: RegisteredModel):
        self.registered = registered
        self.admin = registered.admin
        # Instantiate dependencies — DIP: inject via class attributes
        self.query_provider = self.query_provider_class(registered)
        self.form_parser = self.form_parser_class(registered)
        self.html_renderer = (
            self.html_renderer_class() if self.html_renderer_class else None
        )
        self.api_renderer = (
            self.api_renderer_class(registered)
            if self.api_renderer_class
            else None
        )

    def _get_extra_context(self, request: Request) -> dict[str, Any]:
        """Inject AdminExtra CSS/JS into template context.

        SRP: Only collects extra assets from model admin config.
        """
        extra = getattr(self.admin, "extra", None)
        if extra is None:
            return {}
        admin_path = request.app.state.admin_config.get("admin_path", "/admin")
        return extra.to_context(admin_path)

    def _serialize(self, obj: Any) -> dict[str, Any]:
        """Serialize an object to a dict using registered columns."""
        if self.api_renderer and hasattr(self.api_renderer, "serialize"):
            return self.api_renderer.serialize(obj)
        item_dict: dict[str, Any] = {"id": getattr(obj, "id", None)}
        for col in self.registered.columns:
            if col.name != "id":
                item_dict[col.name] = str(getattr(obj, col.name, ""))
        return item_dict

    async def html_response(self, request: Request, **kwargs) -> Response:
        raise NotImplementedError

    async def api_response(self, request: Request, **kwargs) -> Response:
        raise NotImplementedError


class ListView(BaseView):
    """Orchestrates list view: query -> render HTML or API."""

    html_renderer_class = ListHTMLRenderer
    api_renderer_class = ListAPIRenderer

    def _build_display_columns(self) -> list[DisplayColumn]:
        """Build display column metadata."""
        from sqlalchemy import inspect as sa_inspect

        model = self.registered.model
        mapper = sa_inspect(model)
        rel_names = {r.key for r in mapper.relationships}

        list_display = self.admin.list_display or [
            c.name for c in self.registered.columns if c.name != "id"
        ]

        display_columns = []
        for col_name in list_display:
            label = col_name.replace("_", " ").title()
            display_columns.append(
                DisplayColumn(col_name, label, col_name in rel_names)
            )
        return display_columns

    async def _build_filter_fields(
        self, request: Request
    ) -> dict[str, dict[str, Any]]:
        """Build filter field metadata."""
        if not self.admin.list_filter:
            return {}
        session = request.app.state.admin_db_session
        model = self.registered.model
        filter_fields: dict[str, dict[str, Any]] = {}
        for filter_field in self.admin.list_filter:
            filter_fields[
                filter_field
            ] = await self.query_provider._get_filter_choices(
                model, filter_field, session
            )
        return filter_fields

    async def get_context(
        self, request: Request, q: str, page: int, checker: Any
    ) -> dict[str, Any]:
        """Build template context — override to add custom context."""
        from fastapi_admin.types import PermissionSet
        from fastapi_admin.views.sidebar import inject_sidebar_context

        items, total, page, per_page = await self.query_provider.get_list(
            request, q, page
        )

        active_filters: dict[str, str] = {}
        if self.admin.list_filter:
            for filter_field in self.admin.list_filter:
                val = request.query_params.get(f"filter_{filter_field}", "")
                if val:
                    active_filters[filter_field] = val
                for suffix in ("__gte", "__lte", "__from", "__to"):
                    val = request.query_params.get(
                        f"filter_{filter_field}{suffix}", ""
                    )
                    if val:
                        active_filters[f"{filter_field}{suffix}"] = val

        display_columns = self._build_display_columns()
        filter_fields = await self._build_filter_fields(request)

        template_context = {
            "model": self.registered,
            "registered": self.registered,
            "display_columns": display_columns,
            "items": items,
            "search_query": q,
            "page": page,
            "total_pages": max(1, math.ceil(total / per_page)),
            "total": total,
            "per_page": per_page,
            "filter_fields": filter_fields,
            "active_filters": active_filters,
            "permissions": checker.permission_set(self.registered.table_name)
            if checker
            else PermissionSet(
                can_view=True, can_create=True, can_edit=True, can_delete=True
            ),
            "list_actions": self.admin.get_list_actions(),
            "row_actions": self.admin.get_row_actions(),
            "list_tabs": getattr(self.admin, "list_tabs", []),
            "list_sections": getattr(self.admin, "list_sections", []),
            "ordering_field": getattr(self.admin, "ordering_field", None),
            "hide_ordering_field": getattr(
                self.admin, "hide_ordering_field", False
            ),
            "list_filter_options": getattr(
                self.admin, "list_filter_options", {}
            ),
            "list_filter_horizontal": getattr(
                self.admin, "list_filter_horizontal", False
            ),
        }
        template_context.update(self._get_extra_context(request))
        inject_sidebar_context(request, template_context)
        return template_context

    async def html_response(
        self, request: Request, q: str = "", page: int = 1, **kwargs: Any
    ) -> Response:
        checker = await _resolve_permission_checker(request)
        if checker:
            await checker.load_permissions(self.registered.table_name)
        ctx = await self.get_context(request, q, page, checker)
        return await self.html_renderer.render(request, ctx)

    async def api_response(
        self,
        request: Request,
        page: int = 1,
        per_page: int = 25,
        q: str = "",
        order: str = "",
        **kwargs: Any,
    ) -> Any:
        items, total, page, per_page = await self.query_provider.get_list(
            request, q, page
        )
        item_list = [self._serialize(item) for item in items]
        return await self.api_renderer.render(
            request,
            {
                "items": item_list,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": math.ceil(total / per_page) if per_page else 1,
            },
        )


class CreateView(BaseView):
    """Orchestrates create: parse -> validate -> save -> respond."""

    html_renderer_class = FormHTMLRenderer
    form_parser_class = HTMLFormParser
    api_renderer_class = ItemAPIRenderer

    def _build_form_context(
        self,
        request: Request,
        obj: Any | None = None,
        values: dict[str, Any] | None = None,
        errors: dict[str, list[str]] | None = None,
        is_create: bool = True,
        checker: Any = None,
    ) -> dict[str, Any]:
        """Build form template context."""
        from fastapi_admin.form.pipeline import (
            build_form_context as _build_form_ctx,
        )
        from fastapi_admin.types import PermissionSet
        from fastapi_admin.views.sidebar import inject_sidebar_context

        ctx = _build_form_ctx(
            self.registered,
            obj=obj,
            values=values,
            errors=errors,
            request=request,
            is_create=is_create,
        )
        template_context = {
            "form_context": ctx,
            "registered": self.registered,
            "obj": ctx.obj,
            "form_fields": ctx.fieldsets[0].fields if ctx.fieldsets else [],
            "fieldsets": ctx.fieldsets,
            "errors": ctx.errors,
            "is_create": is_create,
            "permissions": checker.permission_set(self.registered.table_name)
            if checker
            else PermissionSet(
                can_view=True, can_create=True, can_edit=True, can_delete=True
            ),
            "detail_actions": self.admin.get_detail_actions(),
            "submit_line_actions": self.admin.get_submit_line_actions(),
            "conditional_fields": getattr(self.admin, "conditional_fields", {}),
            "warn_unsaved_form": getattr(self.admin, "warn_unsaved_form", True),
            "compressed_fields": getattr(self.admin, "compressed_fields", True),
            "change_form_show_cancel_button": getattr(
                self.admin, "change_form_show_cancel_button", True
            ),
        }
        template_context.update(self._get_extra_context(request))
        inject_sidebar_context(request, template_context)
        return template_context

    async def _create_object(
        self, request: Request, parsed: dict[str, Any]
    ) -> RedirectResponse:
        """Create object in database."""
        session = request.app.state.admin_db_session
        obj = self.registered.model(**parsed)
        self.admin.on_create(obj, request)
        session.add(obj)
        await session.commit()
        self.admin.after_create(obj, request)
        add_flash(
            request, "success", f"{self.registered.verbose_name} created."
        )
        url = (
            f"{request.app.state.admin_config['admin_path']}"
            f"/{self.registered.table_name}/"
        )
        return RedirectResponse(url=url, status_code=303)

    async def html_response(self, request: Request, **kwargs: Any) -> Response:
        checker = await _resolve_permission_checker(request)
        if checker:
            await checker.load_permissions(self.registered.table_name)

        if request.method == "GET":
            ctx = self._build_form_context(
                request, is_create=True, checker=checker
            )
            return await self.html_renderer.render(request, ctx)

        # POST
        parsed, errors = await self.form_parser.parse(request)
        if errors:
            session = request.app.state.admin_db_session
            await session.rollback()
            ctx = self._build_form_context(
                request,
                values=parsed,
                errors=errors,
                is_create=True,
                checker=checker,
            )
            return await self.html_renderer.render(request, ctx)

        return await self._create_object(request, parsed)

    async def api_response(self, request: Request, **kwargs: Any) -> Any:
        parser = JSONBodyParser(self.registered)
        parsed, errors = await parser.parse(request)
        if errors:
            raise HTTPException(status_code=422, detail=errors)
        session = request.app.state.admin_db_session
        obj = self.registered.model(**parsed)
        self.admin.on_create(obj, request)
        session.add(obj)
        await session.commit()
        self.admin.after_create(obj, request)
        return await self.api_renderer.render(request, self._serialize(obj))


class EditView(BaseView):
    """Orchestrates edit: fetch -> parse -> validate -> update -> respond."""

    html_renderer_class = FormHTMLRenderer
    form_parser_class = HTMLFormParser
    api_renderer_class = ItemAPIRenderer

    def _build_form_context(
        self,
        request: Request,
        obj: Any | None = None,
        values: dict[str, Any] | None = None,
        errors: dict[str, list[str]] | None = None,
        is_create: bool = False,
        checker: Any = None,
    ) -> dict[str, Any]:
        """Build form template context."""
        from fastapi_admin.form.pipeline import (
            build_form_context as _build_form_ctx,
        )
        from fastapi_admin.types import PermissionSet
        from fastapi_admin.views.sidebar import inject_sidebar_context

        ctx = _build_form_ctx(
            self.registered,
            obj=obj,
            values=values,
            errors=errors,
            request=request,
            is_create=is_create,
        )
        template_context = {
            "form_context": ctx,
            "registered": self.registered,
            "obj": ctx.obj,
            "form_fields": ctx.fieldsets[0].fields if ctx.fieldsets else [],
            "fieldsets": ctx.fieldsets,
            "errors": ctx.errors,
            "is_create": is_create,
            "permissions": checker.permission_set(self.registered.table_name)
            if checker
            else PermissionSet(
                can_view=True, can_create=True, can_edit=True, can_delete=True
            ),
            "detail_actions": self.admin.get_detail_actions(),
            "submit_line_actions": self.admin.get_submit_line_actions(),
            "conditional_fields": getattr(self.admin, "conditional_fields", {}),
            "warn_unsaved_form": getattr(self.admin, "warn_unsaved_form", True),
            "compressed_fields": getattr(self.admin, "compressed_fields", True),
            "change_form_show_cancel_button": getattr(
                self.admin, "change_form_show_cancel_button", True
            ),
        }
        template_context.update(self._get_extra_context(request))
        inject_sidebar_context(request, template_context)
        return template_context

    async def _update_object(
        self, request: Request, obj: Any, parsed: dict[str, Any]
    ) -> RedirectResponse:
        """Update object in database."""
        self.admin.on_update(obj, parsed, request)
        for key, value in parsed.items():
            setattr(obj, key, value)
        session = request.app.state.admin_db_session
        await session.commit()
        self.admin.after_update(obj, request)
        add_flash(
            request, "success", f"{self.registered.verbose_name} updated."
        )
        url = (
            f"{request.app.state.admin_config['admin_path']}"
            f"/{self.registered.table_name}/"
        )
        return RedirectResponse(url=url, status_code=303)

    async def html_response(
        self, request: Request, id: Any = None, **kwargs: Any
    ) -> Response:
        obj = await self.query_provider.get_object(request, id)
        if not obj:
            raise HTTPException(status_code=404, detail="Not found")

        checker = await _resolve_permission_checker(request)
        if checker:
            await checker.load_permissions(self.registered.table_name)

        if request.method == "GET":
            ctx = self._build_form_context(
                request, obj=obj, is_create=False, checker=checker
            )
            return await self.html_renderer.render(request, ctx)

        # POST
        parsed, errors = await self.form_parser.parse(request, obj=obj)
        if errors:
            session = request.app.state.admin_db_session
            await session.rollback()
            ctx = self._build_form_context(
                request,
                obj=obj,
                values=parsed,
                errors=errors,
                is_create=False,
                checker=checker,
            )
            return await self.html_renderer.render(request, ctx)

        return await self._update_object(request, obj, parsed)

    async def api_response(
        self,
        request: Request,
        id: Any = None,
        item_id: Any = None,
        **kwargs: Any,
    ) -> Any:
        pk = id or item_id
        obj = await self.query_provider.get_object(request, pk)
        if not obj:
            raise HTTPException(status_code=404, detail="Not found")

        if request.method == "GET":
            return self._serialize(obj)

        # PUT
        parser = JSONBodyParser(self.registered)
        parsed, _ = await parser.parse(request, obj)
        self.admin.on_update(obj, parsed, request)
        for key, value in parsed.items():
            setattr(obj, key, value)
        session = request.app.state.admin_db_session
        await session.commit()
        self.admin.after_update(obj, request)
        return self._serialize(obj)


class DeleteView(BaseView):
    """Orchestrates delete: fetch -> delete -> respond."""

    async def html_response(
        self, request: Request, id: Any = None, **kwargs: Any
    ) -> Response:
        obj = await self.query_provider.get_object(request, id)
        if not obj:
            raise HTTPException(status_code=404, detail="Not found")
        try:
            self.admin.on_delete(obj, request)
            session = request.app.state.admin_db_session
            await session.delete(obj)
            await session.commit()
            self.admin.after_delete(obj, request)
            add_flash(
                request, "success", f"{self.registered.verbose_name} deleted."
            )
        except Exception:
            session = request.app.state.admin_db_session
            await session.rollback()
            raise
        url = (
            f"{request.app.state.admin_config['admin_path']}"
            f"/{self.registered.table_name}/"
        )
        return RedirectResponse(url=url, status_code=303)

    async def api_response(
        self,
        request: Request,
        id: Any = None,
        item_id: Any = None,
        **kwargs: Any,
    ) -> Response:
        pk = id or item_id
        obj = await self.query_provider.get_object(request, pk)
        if not obj:
            raise HTTPException(status_code=404, detail="Not found")
        self.admin.on_delete(obj, request)
        session = request.app.state.admin_db_session
        await session.delete(obj)
        await session.commit()
        self.admin.after_delete(obj, request)
        return Response(status_code=204)


class BulkView(BaseView):
    """Orchestrates bulk actions on multiple objects."""

    html_renderer_class = ListHTMLRenderer

    async def html_response(self, request: Request, **kwargs: Any) -> Response:
        session = request.app.state.admin_db_session
        form = await request.form()
        action = form.get("action", "")
        ids = form.getlist("ids[]")

        is_htmx = request.headers.get("HX-Request") == "true"

        if not ids:
            if is_htmx:
                list_view = ListView(self.registered)
                checker = await _resolve_permission_checker(request)
                ctx = await list_view.get_context(request, "", 1, checker)
                return await self.html_renderer.render(request, ctx)
            url = (
                f"{request.app.state.admin_config['admin_path']}"
                f"/{self.registered.table_name}/"
            )
            return RedirectResponse(url=url, status_code=303)

        if action == "delete_selected":
            for pid in ids:
                obj = await session.get(self.registered.model, pid)
                if obj:
                    self.admin.on_delete(obj, request)
                    await session.delete(obj)
            await session.commit()
        else:
            action_fn = getattr(self.admin, f"action_{action}", None)
            if not action_fn:
                raise HTTPException(
                    status_code=400, detail=f"Unknown action: {action}"
                )
            for pid in ids:
                obj = await session.get(self.registered.model, pid)
                if obj:
                    action_fn(obj)
            await session.commit()

        if is_htmx:
            list_view = ListView(self.registered)
            checker = await _resolve_permission_checker(request)
            ctx = await list_view.get_context(request, "", 1, checker)
            return await self.html_renderer.render(request, ctx)

        url = (
            f"{request.app.state.admin_config['admin_path']}"
            f"/{self.registered.table_name}/"
        )
        return RedirectResponse(url=url, status_code=303)

    async def api_response(self, request: Request, **kwargs: Any) -> Any:
        from fastapi.responses import JSONResponse

        session = request.app.state.admin_db_session
        content_type = request.headers.get("content-type", "")
        is_json = content_type.startswith("application/json")
        body = await request.json() if is_json else {}
        action = body.get("action", "")
        ids = body.get("ids", [])

        if action == "delete_selected":
            deleted = 0
            for pid in ids:
                obj = await session.get(self.registered.model, pid)
                if obj:
                    self.admin.on_delete(obj, request)
                    await session.delete(obj)
                    deleted += 1
            await session.commit()
            return JSONResponse({"deleted": deleted})

        action_fn = getattr(self.admin, f"action_{action}", None)
        if not action_fn:
            raise HTTPException(
                status_code=400, detail=f"Unknown action: {action}"
            )

        executed = 0
        for pid in ids:
            obj = await session.get(self.registered.model, pid)
            if obj:
                action_fn(obj)
                executed += 1
        await session.commit()
        return JSONResponse({"executed": executed})


class SearchView(BaseView):
    """Orchestrates search/autocomplete for relation pickers."""

    async def html_response(
        self, request: Request, q: str = "", **kwargs: Any
    ) -> Any:
        return await self._search(request, q)

    async def api_response(
        self, request: Request, q: str = "", **kwargs: Any
    ) -> Any:
        return await self._search(request, q)

    async def _search(self, request: Request, q: str) -> Any:
        from fastapi.responses import JSONResponse
        from sqlalchemy import or_, select

        session = request.app.state.admin_db_session
        model = self.registered.model
        base = select(model)

        clauses = []
        if q:
            search_fields = getattr(self.admin, "search_fields", None) or [
                "name",
                "title",
            ]
            for sf in search_fields:
                if hasattr(model, sf):
                    col = getattr(model, sf)
                    if hasattr(col, "ilike"):
                        clauses.append(col.ilike(f"%{q}%"))

        if clauses:
            base = base.where(or_(*clauses))

        base = base.limit(20)
        result = session.execute(base)
        if hasattr(result, "__await__"):
            result = await result
        rows = result.scalars().all()

        results = []
        for row in rows:
            pk = getattr(row, self.registered.pk_field)
            label = self.admin.__str__(row)
            results.append({"id": str(pk), "label": label})

        return JSONResponse(results)
