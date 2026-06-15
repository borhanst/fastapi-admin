"""ViewFactory — unified factory for CRUD view handlers."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse
from starlette.datastructures import UploadFile

from fastapi_admin.flash import add_flash
from fastapi_admin.registry import RegisteredModel
from fastapi_admin.validation import FormValidator
from fastapi_admin.views.context import ViewContextBuilder
from fastapi_admin.widgets.inputs import FileUploadWidget, ImageUploadWidget

_FILE_WIDGET_TYPES = (FileUploadWidget, ImageUploadWidget)


def _get_storage(request: Request):
    """Get the storage backend from app.state, or None."""
    return getattr(request.app.state, "admin_storage", None)


async def _resolve_permission_checker(request: Request) -> Any:
    """Resolve a PermissionChecker for the current request.

    Returns None if the user is not authenticated or the checker cannot be built.
    """
    from sqlalchemy import select

    from fastapi_admin.auth.permissions import PermissionChecker

    session_backend = getattr(request.app.state, "admin_session_backend", None)
    if session_backend is None:
        return None

    token = request.cookies.get(session_backend.cookie_name)
    session_payload = session_backend.decode(token) if token else None
    if session_payload is None:
        return None

    user_id = session_payload.get("user_id")
    if user_id is None:
        return None

    async_session = getattr(request.app.state, "admin_db_session", None)
    if async_session is None:
        return None

    # Cache the user on app.state to avoid re-loading per request
    cached_user = getattr(request.app.state, "_admin_permission_user", None)
    if cached_user is None or getattr(cached_user, "id", None) != user_id:
        from fastapi_admin.auth.models import AdminUser

        result = await async_session.execute(
            select(AdminUser).where(AdminUser.id == user_id, AdminUser.is_active == True)
        )
        user = result.scalar_one_or_none()
        if user is None:
            return None
        request.app.state._admin_permission_user = user
        cached_user = user

    return PermissionChecker(session=async_session, user=cached_user)


async def _handle_file_field(
    request: Request,
    widget: Any,
    field_meta: Any,
    form_data: Any,
    obj: Any | None,
    action: str | None,
    parsed: dict[str, Any],
    errors: dict[str, list[str]],
) -> None:
    """Handle a file upload field during form submission."""
    storage = _get_storage(request)
    field_name = field_meta.name
    raw = form_data.get(field_name)

    if isinstance(raw, UploadFile) and raw.filename:
        if widget.max_size_mb is not None:
            content = await raw.read()
            max_bytes = int(widget.max_size_mb * 1024 * 1024)
            if len(content) > max_bytes:
                errors[field_name] = [
                    f"File size exceeds maximum allowed size ({widget.max_size_mb} MB)."
                ]
                await raw.seek(0)
                return
            await raw.seek(0)

        if storage is None:
            errors[field_name] = ["No storage backend configured."]
            return

        try:
            path = await storage.save(raw, directory=field_meta.name)
        except ValueError as exc:
            errors[field_name] = [str(exc)]
            return

        if action == "replace" and obj is not None:
            old_path = getattr(obj, field_name, None)
            if old_path:
                await storage.delete(old_path)

        parsed[field_name] = path

    elif action == "clear":
        if storage is not None and obj is not None:
            old_path = getattr(obj, field_name, None)
            if old_path:
                await storage.delete(old_path)
        parsed[field_name] = None

    elif action == "keep" or action is None:
        if obj is not None:
            parsed[field_name] = getattr(obj, field_name, None)

    else:
        if obj is not None:
            parsed[field_name] = getattr(obj, field_name, None)


class ViewFactory:
    """Unified factory for creating CRUD view handlers.

    Centralizes view creation logic that was previously duplicated across
    multiple standalone factory functions.
    """

    def __init__(
        self,
        context_builder: ViewContextBuilder | None = None,
        form_pipeline: Any = None,
        validation_engine: Any = None,
    ):
        self.context_builder = context_builder or ViewContextBuilder()
        self.form_pipeline = form_pipeline
        self.validation_engine = validation_engine or FormValidator()

    async def _parse_form_fields(
        self,
        registered: RegisteredModel,
        form_data: Any,
        request: Request,
        obj: Any | None = None,
    ) -> tuple[dict[str, Any], dict[str, list[str]]]:
        """Parse and validate form fields from request data.

        Returns (parsed_values, errors).
        """
        parsed: dict[str, Any] = {}
        errors: dict[str, list[str]] = {}

        for field_meta in registered.form_fields:
            if field_meta.readonly:
                continue
            widget = registered.get_widget(field_meta.name)

            if isinstance(widget, _FILE_WIDGET_TYPES):
                action = form_data.get(f"_action_{field_meta.name}", "keep") if obj else None
                await _handle_file_field(
                    request, widget, field_meta, form_data,
                    obj=obj, action=action,
                    parsed=parsed, errors=errors,
                )
                if obj is None and field_meta.name not in errors and field_meta.name not in parsed:
                    parsed[field_meta.name] = None
                continue

            raw = form_data.get(field_meta.name)
            value = widget.parse(raw)
            field_errors = widget.validate(value, field_meta)
            if field_errors:
                errors[field_meta.name] = field_errors
            else:
                parsed[field_meta.name] = value

        if not errors:
            errors = self.validation_engine.run(registered, parsed, obj=obj)

        return parsed, errors

    def create_list_view(self, registered: RegisteredModel):
        """Create a list view handler for the given registered model."""
        async def list_view(request: Request, q: str = "", page: int = 1, _: Any = None):
            templates = request.app.state.admin_jinja_env
            checker = await _resolve_permission_checker(request)
            if checker:
                await checker.load_permissions(registered.table_name)
            ctx = await self.context_builder.build_list_context(
                registered, request, q=q, page=page, permission_checker=checker
            )
            return templates.TemplateResponse(request, "pages/list.html", ctx)
        list_view.__name__ = f"list_{registered.table_name}"
        return list_view

    def create_create_form_view(self, registered: RegisteredModel):
        """Create a form display handler for creating new objects."""
        async def create_form(request: Request, _: Any = None):
            templates = request.app.state.admin_jinja_env
            checker = await _resolve_permission_checker(request)
            if checker:
                await checker.load_permissions(registered.table_name)
            ctx = self.context_builder.build_form_context(
                registered, request, is_create=True, permission_checker=checker
            )
            return templates.TemplateResponse(request, "pages/form.html", ctx)
        create_form.__name__ = f"create_form_{registered.table_name}"
        return create_form

    def create_create_submit_view(self, registered: RegisteredModel):
        """Create a form submission handler for creating new objects."""
        async def create_submit(request: Request, _: Any = None):
            templates = request.app.state.admin_jinja_env
            session = request.app.state.admin_db_session
            form_data = await request.form()
            checker = await _resolve_permission_checker(request)
            if checker:
                await checker.load_permissions(registered.table_name)

            parsed, errors = await self._parse_form_fields(
                registered, form_data, request, obj=None
            )

            if errors:
                ctx = self.context_builder.build_form_context(
                    registered, request, values=parsed, errors=errors, is_create=True,
                    permission_checker=checker,
                )
                return templates.TemplateResponse(request, "pages/form.html", ctx, status_code=422)

            obj = registered.model(**parsed)
            registered.admin.on_create(obj, request)
            session.add(obj)
            await session.commit()
            registered.admin.after_create(obj, request)
            add_flash(request, "success", f"{registered.verbose_name} created.")
            url = f"{request.app.state.admin_config['admin_path']}/{registered.table_name}/"
            return RedirectResponse(url=url, status_code=303)
        create_submit.__name__ = f"create_submit_{registered.table_name}"
        return create_submit

    def create_edit_form_view(self, registered: RegisteredModel):
        """Create a form display handler for editing existing objects."""
        async def edit_form(request: Request, id: str, _: Any = None):
            templates = request.app.state.admin_jinja_env
            session = request.app.state.admin_db_session
            obj = await session.get(registered.model, id)
            if not obj:
                raise HTTPException(status_code=404, detail="Not found")
            checker = await _resolve_permission_checker(request)
            if checker:
                await checker.load_permissions(registered.table_name)
            ctx = self.context_builder.build_form_context(
                registered, request, obj=obj, is_create=False, permission_checker=checker
            )
            return templates.TemplateResponse(request, "pages/form.html", ctx)
        edit_form.__name__ = f"edit_form_{registered.table_name}"
        return edit_form

    def create_edit_submit_view(self, registered: RegisteredModel):
        """Create a form submission handler for editing existing objects."""
        async def edit_submit(request: Request, id: str, _: Any = None):
            templates = request.app.state.admin_jinja_env
            session = request.app.state.admin_db_session
            obj = await session.get(registered.model, id)
            if not obj:
                raise HTTPException(status_code=404, detail="Not found")
            form_data = await request.form()
            checker = await _resolve_permission_checker(request)
            if checker:
                await checker.load_permissions(registered.table_name)

            parsed, errors = await self._parse_form_fields(
                registered, form_data, request, obj=obj
            )

            if errors:
                ctx = self.context_builder.build_form_context(
                    registered, request, obj=obj, values=parsed, errors=errors, is_create=False,
                    permission_checker=checker,
                )
                return templates.TemplateResponse(request, "pages/form.html", ctx, status_code=422)

            registered.admin.on_update(obj, parsed, request)
            for key, value in parsed.items():
                setattr(obj, key, value)
            await session.commit()
            registered.admin.after_update(obj, request)
            add_flash(request, "success", f"{registered.verbose_name} updated.")
            url = f"{request.app.state.admin_config['admin_path']}/{registered.table_name}/"
            return RedirectResponse(url=url, status_code=303)
        edit_submit.__name__ = f"edit_submit_{registered.table_name}"
        return edit_submit

    def create_delete_view(self, registered: RegisteredModel):
        """Create a delete handler for removing objects."""
        async def delete_submit(request: Request, id: str, _: Any = None):
            session = request.app.state.admin_db_session
            obj = await session.get(registered.model, id)
            if not obj:
                raise HTTPException(status_code=404, detail="Not found")
            registered.admin.on_delete(obj, request)
            await session.delete(obj)
            await session.commit()
            registered.admin.after_delete(obj, request)
            add_flash(request, "success", f"{registered.verbose_name} deleted.")
            url = f"{request.app.state.admin_config['admin_path']}/{registered.table_name}/"
            return RedirectResponse(url=url, status_code=303)
        delete_submit.__name__ = f"delete_{registered.table_name}"
        return delete_submit

    def create_bulk_view(self, registered: RegisteredModel):
        """Create a bulk action handler for multiple objects."""
        async def bulk_action(request: Request, _: Any = None):
            session = request.app.state.admin_db_session
            form = await request.form()
            action = form.get("action", "")
            ids = form.getlist("ids[]")
            if not ids:
                url = f"{request.app.state.admin_config['admin_path']}/{registered.table_name}/"
                return RedirectResponse(url=url, status_code=303)
            if action == "delete_selected":
                for pid in ids:
                    obj = await session.get(registered.model, pid)
                    if obj:
                        registered.admin.on_delete(obj, request)
                        await session.delete(obj)
                await session.commit()
                msg = f"{len(ids)} {registered.verbose_name_plural} deleted."
                add_flash(request, "success", msg)
            else:
                action_fn = getattr(registered.admin, f"action_{action}", None)
                if not action_fn:
                    raise HTTPException(
                        status_code=400, detail=f"Unknown action: {action}"
                    )
                for pid in ids:
                    obj = await session.get(registered.model, pid)
                    if obj:
                        action_fn(obj)
                await session.commit()
                add_flash(request, "success", f"Action '{action}' applied to {len(ids)} records.")
            url = f"{request.app.state.admin_config['admin_path']}/{registered.table_name}/"
            return RedirectResponse(url=url, status_code=303)
        bulk_action.__name__ = f"bulk_{registered.table_name}"
        return bulk_action

    def create_all_views(self, registered: RegisteredModel) -> dict[str, Any]:
        """Create all standard CRUD views for a registered model.

        Returns a dict mapping view names to handler functions.
        """
        return {
            "list": self.create_list_view(registered),
            "create_form": self.create_create_form_view(registered),
            "create_submit": self.create_create_submit_view(registered),
            "edit_form": self.create_edit_form_view(registered),
            "edit_submit": self.create_edit_submit_view(registered),
            "delete": self.create_delete_view(registered),
            "bulk": self.create_bulk_view(registered),
        }
