"""Role management views — list, create, edit, delete."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select

from fastapi_admin.admin import Admin
from fastapi_admin.auth.dependencies import get_current_admin_user
from fastapi_admin.auth.models import AdminFieldPermission, AdminPermission, AdminRole, AdminUser
from fastapi_admin.registry import AdminRegistry
from fastapi_admin.auth.protocol import AdminUserProtocol


router = APIRouter()


async def _require_superuser(
    user: AdminUserProtocol = Depends(get_current_admin_user),
) -> AdminUserProtocol:
    if not getattr(user, "is_superuser", False):
        raise HTTPException(status_code=403, detail="Superuser access required.")
    return user


@router.get("/roles", response_class=HTMLResponse)
async def role_list_view(
    request: Request,
    _: AdminUserProtocol = Depends(_require_superuser),
):
    """List roles with user counts."""
    templates = request.app.state.admin_jinja_env
    session = request.app.state.admin_db_session

    result = await session.execute(select(AdminRole))
    roles = list(result.scalars().all())

    role_data = []
    for role in roles:
        user_count = len(role.users)
        role_data.append({
            "role": role,
            "user_count": user_count,
        })

    return templates.TemplateResponse(
        request,
        "pages/roles/list.html",
        {
            "roles": role_data,
        },
    )


@router.get("/roles/create", response_class=HTMLResponse)
async def role_create_view(
    request: Request,
    _: AdminUserProtocol = Depends(_require_superuser),
):
    """Show empty role create form."""
    templates = request.app.state.admin_jinja_env
    registry = request.app.state.admin_registry

    models = registry.all()
    return templates.TemplateResponse(
        request,
        "pages/roles/form.html",
        {
            "role": None,
            "models": models,
            "permissions": {},
            "field_permissions": {},
        },
    )


@router.get("/roles/{role_id}", response_class=HTMLResponse)
async def role_edit_view(
    request: Request,
    role_id: int,
    _: AdminUserProtocol = Depends(_require_superuser),
):
    """Show edit form with permission matrix."""
    templates = request.app.state.admin_jinja_env
    session = request.app.state.admin_db_session
    registry = request.app.state.admin_registry

    role = await session.get(AdminRole, role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")

    models = registry.all()

    perms = (await session.execute(select(AdminPermission).where(AdminPermission.role_id == role_id))).scalars().all()
    f_perms = (await session.execute(select(AdminFieldPermission).where(AdminFieldPermission.role_id == role_id))).scalars().all()

    perm_map = {(p.table_name): p for p in perms}
    f_perms_map = {}
    for fp in f_perms:
        if fp.table_name not in f_perms_map:
            f_perms_map[fp.table_name] = {}
        f_perms_map[fp.table_name][fp.field_name] = fp

    return templates.TemplateResponse(
        request,
        "pages/roles/form.html",
        {
            "role": role,
            "models": models,
            "permissions": perm_map,
            "field_permissions": f_perms_map,
        },
    )


@router.post("/roles/{role_id}", response_class=HTMLResponse)
async def role_save_view(
    request: Request,
    role_id: int,
    _: AdminUserProtocol = Depends(_require_superuser),
):
    """Save role permissions from form submission."""
    session = request.app.state.admin_db_session
    registry = request.app.state.admin_registry

    role = await session.get(AdminRole, role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")

    form = await request.form()
    perm_data: dict[str, dict[str, str]] = {}
    field_perm_data: dict[str, dict[str, dict[str, str]]] = {}

    for key, value in form.multi_items():
        if key.startswith("perm[") and key.endswith("]"):
            inner = key[5:-1]
            table, action = inner.split("][")
            perm_data.setdefault(table, {})[action] = value
        elif key.startswith("field_perm[") and key.endswith("]"):
            inner = key[11:-1]
            parts = inner.split("][")
            if len(parts) == 3:
                table, field, mode = parts
                field_perm_data.setdefault(table, {}).setdefault(field, {})[mode] = value

    existing_perms = (await session.execute(select(AdminPermission).where(AdminPermission.role_id == role_id))).scalars().all()
    existing_perm_map = {p.table_name: p for p in existing_perms}

    for table, data in perm_data.items():
        if table in existing_perm_map:
            perm = existing_perm_map[table]
            perm.can_view = data.get("view") == "on"
            perm.can_create = data.get("create") == "on"
            perm.can_edit = data.get("edit") == "on"
            perm.can_delete = data.get("delete") == "on"
        else:
            perm = AdminPermission(
                role_id=role_id,
                table_name=table,
                can_view=data.get("view") == "on",
                can_create=data.get("create") == "on",
                can_edit=data.get("edit") == "on",
                can_delete=data.get("delete") == "on",
            )
            session.add(perm)

    await session.flush()

    await session.execute(select(AdminFieldPermission).where(AdminFieldPermission.role_id == role_id).delete())
    for table, fields in field_perm_data.items():
        for field, modes in fields.items():
            f_perm = AdminFieldPermission(
                role_id = role_id,
                table_name = table,
                field_name = field,
                can_view = modes.get("view") == "on",
                can_edit = modes.get("edit") == "on",
            )
            session.add(f_perm)

    await session.commit()

    return RedirectResponse(url="/admin/roles", status_code=302)


@router.post("/roles/{role_id}/delete", response_class=RedirectResponse)
async def role_delete_view(
    request: Request,
    role_id: int,
    _: AdminUserProtocol = Depends(_require_superuser),
):
    """Delete role (refuse if users assigned)."""
    session = request.app.state.admin_db_session

    role = await session.get(AdminRole, role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")

    user_count = len(role.users)
    if user_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete role. {user_count} user(s) are still assigned.",
        )

    await session.delete(role)
    await session.commit()

    return RedirectResponse(url="/admin/roles", status_code=302)
