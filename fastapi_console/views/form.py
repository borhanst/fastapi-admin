"""Create and edit form handler factories."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse
from starlette.datastructures import UploadFile

from fastapi_console.flash import add_flash
from fastapi_console.form.pipeline import build_form_context
from fastapi_console.registry import RegisteredModel
from fastapi_console.types import PermissionSet
from fastapi_console.views.sidebar import inject_sidebar_context
from fastapi_console.validation import FormValidator
from fastapi_console.widgets.inputs import FileUploadWidget, ImageUploadWidget

# Widgets that handle file uploads
_FILE_WIDGET_TYPES = (FileUploadWidget, ImageUploadWidget)


def _get_storage(request: Request):
    """Get the storage backend from app.state, or None."""
    return getattr(request.app.state, "admin_storage", None)


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
    """Handle a file upload field during form submission.

    For create: always save the new upload.
    For edit: respect the ``action`` parameter:
      - ``keep`` (default): keep existing file path unchanged
      - ``replace``: save new upload, delete old file
      - ``clear``: delete old file, set value to None
    """
    storage = _get_storage(request)
    field_name = field_meta.name
    raw = form_data.get(field_name)

    if isinstance(raw, UploadFile) and raw.filename:
        # New file uploaded
        if widget.max_size_mb is not None:
            content = await raw.read()
            max_bytes = int(widget.max_size_mb * 1024 * 1024)
            if len(content) > max_bytes:
                errors[field_name] = [
                    f"File size exceeds maximum allowed size ({widget.max_size_mb} MB)."
                ]
                # Reset file position for potential re-read
                await raw.seek(0)
                return
            # Reset file position after size check
            await raw.seek(0)

        if storage is None:
            errors[field_name] = ["No storage backend configured."]
            return

        try:
            path = await storage.save(raw, directory=field_meta.name)
        except ValueError as exc:
            errors[field_name] = [str(exc)]
            return

        # Delete old file if replacing
        if action == "replace" and obj is not None:
            old_path = getattr(obj, field_name, None)
            if old_path:
                await storage.delete(old_path)

        parsed[field_name] = path

    elif action == "clear":
        # User wants to remove the file
        if storage is not None and obj is not None:
            old_path = getattr(obj, field_name, None)
            if old_path:
                await storage.delete(old_path)
        parsed[field_name] = None

    elif action == "keep" or action is None:
        # Keep existing value
        if obj is not None:
            parsed[field_name] = getattr(obj, field_name, None)

    else:
        # No new upload, no explicit action — keep existing
        if obj is not None:
            parsed[field_name] = getattr(obj, field_name, None)


def create_form_factory(registered: RegisteredModel):
    async def create_form(request: Request, _: Any = None):
        templates = request.app.state.admin_jinja_env
        ctx = build_form_context(registered, is_create=True)
        return templates.TemplateResponse(request, "pages/form.html", inject_sidebar_context(request, {
            "form_context": ctx,
            "is_create": True,
            "permissions": PermissionSet(
                can_view=True, can_create=True, can_edit=True, can_delete=True
            ),
        }))
    create_form.__name__ = f"create_form_{registered.table_name}"
    return create_form


def create_submit_factory(registered: RegisteredModel):
    async def create_submit(request: Request, _: Any = None):
        templates = request.app.state.admin_jinja_env
        session = request.app.state.admin_db_session
        form_data = await request.form()
        parsed: dict[str, Any] = {}
        errors: dict[str, list[str]] = {}

        for field_meta in registered.form_fields:
            if field_meta.readonly:
                continue
            widget = registered.get_widget(field_meta.name)

            if isinstance(widget, _FILE_WIDGET_TYPES):
                await _handle_file_field(
                    request, widget, field_meta, form_data,
                    obj=None, action=None,
                    parsed=parsed, errors=errors,
                )
                if field_meta.name not in errors and field_meta.name not in parsed:
                    # No upload and not required — set None
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
            validator = FormValidator()
            errors = validator.run(registered, parsed, obj=None)

        if errors:
            ctx = build_form_context(
                registered, values=parsed, errors=errors, is_create=True
            )
            return templates.TemplateResponse(request, "pages/form.html", inject_sidebar_context(request, {
                "form_context": ctx,
                "is_create": True,
            }), status_code=422)

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


def edit_form_factory(registered: RegisteredModel):
    async def edit_form(request: Request, id: str, _: Any = None):
        templates = request.app.state.admin_jinja_env
        session = request.app.state.admin_db_session
        obj = await session.get(registered.model, id)
        if not obj:
            raise HTTPException(status_code=404, detail="Not found")
        form_ctx = build_form_context(registered, obj=obj, is_create=False)
        return templates.TemplateResponse(request, "pages/form.html", inject_sidebar_context(request, {
            "form_context": form_ctx,
            "is_create": False,
        }))
    edit_form.__name__ = f"edit_form_{registered.table_name}"
    return edit_form


def edit_submit_factory(registered: RegisteredModel):
    async def edit_submit(request: Request, id: str, _: Any = None):
        templates = request.app.state.admin_jinja_env
        session = request.app.state.admin_db_session
        obj = await session.get(registered.model, id)
        if not obj:
            raise HTTPException(status_code=404, detail="Not found")
        form_data = await request.form()
        parsed: dict[str, Any] = {}
        errors: dict[str, list[str]] = {}

        for field_meta in registered.form_fields:
            if field_meta.readonly:
                continue
            widget = registered.get_widget(field_meta.name)

            if isinstance(widget, _FILE_WIDGET_TYPES):
                action = form_data.get(f"_action_{field_meta.name}", "keep")
                await _handle_file_field(
                    request, widget, field_meta, form_data,
                    obj=obj, action=action,
                    parsed=parsed, errors=errors,
                )
                continue

            raw = form_data.get(field_meta.name)
            value = widget.parse(raw)
            field_errors = widget.validate(value, field_meta)
            if field_errors:
                errors[field_meta.name] = field_errors
            else:
                parsed[field_meta.name] = value

        if not errors:
            validator = FormValidator()
            errors = validator.run(registered, parsed, obj=obj)

        if errors:
            ctx = build_form_context(
                registered, obj=obj, values=parsed, errors=errors, is_create=False
            )
            return templates.TemplateResponse(request, "pages/form.html", inject_sidebar_context(request, {
                "form_context": ctx,
                "is_create": False,
            }), status_code=422)

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
