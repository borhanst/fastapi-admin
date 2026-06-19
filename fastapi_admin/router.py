"""Auto-route generation per registered model with RBAC."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from fastapi_admin.auth.csrf import require_csrf_token
from fastapi_admin.auth.dependencies import require_permission
from fastapi_admin.registry import RegisteredModel
from fastapi_admin.views import (
    bulk_factory,
    create_form_factory,
    create_submit_factory,
    delete_factory,
    edit_form_factory,
    edit_submit_factory,
    list_view_factory,
    search_factory,
)


def build_model_router(registered: RegisteredModel) -> APIRouter:
    router = APIRouter(prefix=f"/{registered.table_name}")

    router.add_api_route(
        "/",
        list_view_factory(registered),
        methods=["GET"],
        dependencies=[Depends(require_permission(registered.table_name, "view"))],
    )
    router.add_api_route(
        "/create",
        create_form_factory(registered),
        methods=["GET"],
        dependencies=[Depends(require_permission(registered.table_name, "create"))],
    )
    router.add_api_route(
        "/create",
        create_submit_factory(registered),
        methods=["POST"],
        dependencies=[
            Depends(require_permission(registered.table_name, "create")),
            Depends(require_csrf_token),
        ],
    )
    router.add_api_route(
        "/search",
        search_factory(registered),
        methods=["GET"],
        dependencies=[Depends(require_permission(registered.table_name, "view"))],
    )
    router.add_api_route(
        "/bulk",
        bulk_factory(registered),
        methods=["POST"],
        dependencies=[
            Depends(require_permission(registered.table_name, "edit")),
            Depends(require_csrf_token),
        ],
    )

    @router.post("/validate-field")
    async def validate_field_endpoint(
        request: Request,
        _csrf: bool = Depends(require_csrf_token),
    ):
        templates = request.app.state.admin_jinja_env
        form = await request.form()
        field_name = form.get("field_name")
        raw_value = form.get(field_name)

        field_meta = next(
            (f for f in registered.form_fields if f.name == field_name), None
        )
        if field_meta is None:
            raise HTTPException(status_code=422, detail="Field not found")

        widget = registered.get_widget(field_name)
        parsed = widget.parse(raw_value)
        errors = widget.validate(parsed, field_meta)

        validator_fn = getattr(registered.admin, f"validate_{field_name}", None)
        if validator_fn and not errors:
            err = validator_fn(parsed, obj=None)
            if err:
                errors = [err]

        from fastapi_admin.types import FieldRenderContext

        field_ctx = FieldRenderContext(
            meta=field_meta,
            widget_macro=widget.macro_name,
            widget_context=widget.render_context(field_meta, raw_value),
            errors=errors,
        )
        return templates.TemplateResponse(request, "partials/field_wrapper.html", {
            "field_ctx": field_ctx,
            "model_name": registered.table_name,
        })

    router.add_api_route(
        "/{id}",
        edit_form_factory(registered),
        methods=["GET"],
        dependencies=[Depends(require_permission(registered.table_name, "edit"))],
    )
    router.add_api_route(
        "/{id}",
        edit_submit_factory(registered),
        methods=["POST"],
        dependencies=[
            Depends(require_permission(registered.table_name, "edit")),
            Depends(require_csrf_token),
        ],
    )
    router.add_api_route(
        "/{id}/delete",
        delete_factory(registered),
        methods=["POST"],
        dependencies=[
            Depends(require_permission(registered.table_name, "delete")),
            Depends(require_csrf_token),
        ],
    )

    @router.patch("/{id}/field")
    async def update_field(
        request: Request,
        id: str,
        _csrf: bool = Depends(require_csrf_token),
    ):
        """Inline field update — used by toggle switches in list view."""
        from fastapi_admin.auth.csrf import generate_csrf_token, _get_secret_key

        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            body = await request.json()
        else:
            form = await request.form()
            body = dict(form)

        field_name = body.get("field")
        new_value = body.get("value")

        if not field_name:
            raise HTTPException(status_code=400, detail="Missing field name")

        # Only allow editing fields that are not readonly
        readonly = getattr(registered.admin, "readonly_fields", []) or []
        if field_name in readonly:
            raise HTTPException(status_code=403, detail="Field is read-only")

        # Validate field exists on model
        col = next((c for c in registered.columns if c.name == field_name), None)
        if col is None:
            raise HTTPException(status_code=400, detail="Invalid field name")

        # Parse boolean values
        if col.type.__class__.__name__ == "Boolean":
            new_value = str(new_value).lower() in ("true", "1", "yes")

        session = request.app.state.admin_db_session
        try:
            obj = await session.get(registered.model, id)
            if obj is None:
                raise HTTPException(status_code=404, detail="Object not found")

            setattr(obj, field_name, new_value)
            await session.commit()
        except Exception:
            await session.rollback()
            raise

        # Return updated toggle HTML
        val = getattr(obj, field_name)
        secret = _get_secret_key(request) or ""
        csrf_token = generate_csrf_token(secret)
        admin_path = request.app.state.admin_config["admin_path"]

        if val:
            toggle_html = (
                f'<button class="toggle-switch toggle-switch--on"'
                f' hx-patch="{admin_path}/{registered.table_name}/{obj.id}/field"'
                f' hx-vals=\'{{"field": "{field_name}", "value": "false"}}\''
                f' hx-target="this" hx-swap="outerHTML"'
                f' hx-headers=\'{{"X-CSRF-Token": "{csrf_token}"}}\''
                f' role="checkbox" aria-checked="true">'
                f'<span class="toggle-switch__thumb"></span></button>'
            )
        else:
            toggle_html = (
                f'<button class="toggle-switch"'
                f' hx-patch="{admin_path}/{registered.table_name}/{obj.id}/field"'
                f' hx-vals=\'{{"field": "{field_name}", "value": "true"}}\''
                f' hx-target="this" hx-swap="outerHTML"'
                f' hx-headers=\'{{"X-CSRF-Token": "{csrf_token}"}}\''
                f' role="checkbox" aria-checked="false">'
                f'<span class="toggle-switch__thumb"></span></button>'
            )
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=toggle_html)

    return router
