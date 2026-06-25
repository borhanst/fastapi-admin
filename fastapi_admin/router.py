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

    return router
