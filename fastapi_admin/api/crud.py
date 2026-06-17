"""JSON CRUD handlers for the Admin API."""

from __future__ import annotations

import math
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from sqlalchemy import asc, desc, func, or_, select

from fastapi_admin.api.schemas import PaginatedResponse


async def _get_current_user(request: Request) -> Any:
    """Extract and validate the current user from a Bearer token.

    Delegates credential decode + user loading to
    :mod:`fastapi_admin.auth.identity`, the single current-user seam — so the
    JWT API now honours the ``AuthBackend.get_user`` seam like the cookie path
    and supports BYO user models, not just the built-in ``AdminUser``.
    """
    from fastapi_admin.auth.identity import get_current_user_from_bearer

    user = await get_current_user_from_bearer(request)
    if user is None:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=401, detail="Missing or invalid Authorization header."
            )
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    return user


async def _check_permission(request: Request, user: Any, table_name: str, action: str) -> None:
    """Check if user has permission for the given action. Raises 403 if not."""
    if getattr(user, "is_superuser", False):
        return

    from fastapi_admin.auth.permissions import PermissionChecker

    db_session = request.app.state.admin_db_session
    checker = PermissionChecker(session=db_session, user=user)
    has_perm = await checker.has_permission(table_name, action)
    if not has_perm:
        raise HTTPException(
            status_code=403,
            detail=f"You do not have permission to {action} {table_name}.",
        )


def build_api_router(registry: Any) -> APIRouter:
    """Build the CRUD API router for all registered models.

    Returns a FastAPI APIRouter with endpoints for each registered model.
    """
    router = APIRouter(tags=["api-crud"])

    for registered in registry.all():
        _register_model_routes(router, registered)

    return router


def _register_model_routes(router: APIRouter, registered: Any) -> None:
    """Register CRUD routes for a single model."""
    table_name = registered.table_name
    model = registered.model
    prefix = f"/{table_name}"

    # GET /{model}/ — list with pagination
    @router.get(prefix, response_model=PaginatedResponse)
    async def list_items(
        request: Request,
        page: int = Query(1, ge=1),
        per_page: int = Query(25, ge=1, le=100),
        q: str = Query(""),
        order: str = Query(""),
    ):
        user = await _get_current_user(request)
        await _check_permission(request, user, table_name, "view")
        session = request.app.state.admin_db_session

        base = select(model)

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

        # Count
        count_q = select(func.count()).select_from(base.subquery())
        total = (await session.execute(count_q)).scalar() or 0

        # Ordering
        if order:
            desc_flag = order.startswith("-")
            col_name = order.lstrip("-")
            if hasattr(model, col_name):
                col = getattr(model, col_name)
                base = base.order_by(desc(col) if desc_flag else asc(col))
        elif registered.admin.ordering:
            col_name = registered.admin.ordering[0].lstrip("-")
            if hasattr(model, col_name):
                col = getattr(model, col_name)
                desc_flag = registered.admin.ordering[0].startswith("-")
                base = base.order_by(desc(col) if desc_flag else asc(col))

        # Pagination
        total_pages = max(1, math.ceil(total / per_page))
        page = max(1, min(page, total_pages))
        offset = (page - 1) * per_page
        base = base.offset(offset).limit(per_page)

        result = await session.execute(base)
        items = result.unique().scalars().all()

        # Serialize items to dicts
        item_list = []
        for item in items:
            item_dict = {"id": getattr(item, "id", None)}
            for col in registered.columns:
                if col.name != "id":
                    item_dict[col.name] = str(getattr(item, col.name, ""))
            item_list.append(item_dict)

        return PaginatedResponse(
            items=item_list,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
        )

    # GET /{model}/{id} — retrieve single item
    @router.get(f"{prefix}/{{item_id}}")
    async def retrieve_item(
        request: Request,
        item_id: str,
    ):
        user = await _get_current_user(request)
        await _check_permission(request, user, table_name, "view")
        session = request.app.state.admin_db_session

        obj = await session.get(model, item_id)
        if obj is None:
            raise HTTPException(status_code=404, detail="Not found.")

        item_dict = {"id": getattr(obj, "id", None)}
        for col in registered.columns:
            if col.name != "id":
                item_dict[col.name] = str(getattr(obj, col.name, ""))
        return item_dict

    # POST /{model}/ — create
    @router.post(prefix, status_code=201)
    async def create_item(
        request: Request,
    ):
        user = await _get_current_user(request)
        await _check_permission(request, user, table_name, "create")
        session = request.app.state.admin_db_session
        body = await request.json()

        # Filter to known columns
        valid_fields = {col.name for col in registered.columns}
        filtered = {
            k: v for k, v in body.items() if k in valid_fields and k != "id"
        }

        obj = model(**filtered)
        registered.admin.on_create(obj, request)
        session.add(obj)
        await session.commit()

        item_dict = {"id": getattr(obj, "id", None)}
        for col in registered.columns:
            if col.name != "id":
                item_dict[col.name] = str(getattr(obj, col.name, ""))
        return item_dict

    # PUT /{model}/{id} — update
    @router.put(f"{prefix}/{{item_id}}")
    async def update_item(
        request: Request,
        item_id: str,
    ):
        user = await _get_current_user(request)
        await _check_permission(request, user, table_name, "edit")
        session = request.app.state.admin_db_session

        obj = await session.get(model, item_id)
        if obj is None:
            raise HTTPException(status_code=404, detail="Not found.")

        body = await request.json()
        valid_fields = {col.name for col in registered.columns}
        filtered = {
            k: v for k, v in body.items() if k in valid_fields and k != "id"
        }

        registered.admin.on_update(obj, filtered, request)
        for key, value in filtered.items():
            setattr(obj, key, value)
        await session.commit()

        item_dict = {"id": getattr(obj, "id", None)}
        for col in registered.columns:
            if col.name != "id":
                item_dict[col.name] = str(getattr(obj, col.name, ""))
        return item_dict

    # DELETE /{model}/{id} — delete
    @router.delete(f"{prefix}/{{item_id}}", status_code=204)
    async def delete_item(
        request: Request,
        item_id: str,
    ):
        user = await _get_current_user(request)
        await _check_permission(request, user, table_name, "delete")
        session = request.app.state.admin_db_session

        obj = await session.get(model, item_id)
        if obj is None:
            raise HTTPException(status_code=404, detail="Not found.")

        registered.admin.on_delete(obj, request)
        await session.delete(obj)
        await session.commit()
        return None
