"""Admin user management views — list, create, edit, delete."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select

from fastapi_console.auth.csrf import require_csrf_token
from fastapi_console.auth.dependencies import get_current_admin_user
from fastapi_console.auth.models import AdminRole, AdminUser
from fastapi_console.auth.protocol import AdminUserProtocol
from fastapi_console.db import get_db_session
from fastapi_console.views.sidebar import inject_sidebar_context

router = APIRouter()


async def _require_superuser(
    user: AdminUserProtocol = Depends(get_current_admin_user),
) -> AdminUserProtocol:
    if not getattr(user, "is_superuser", False):
        raise HTTPException(
            status_code=403, detail="Superuser access required."
        )
    return user


@router.get("/users", response_class=HTMLResponse)
async def user_list_view(
    request: Request,
    _: AdminUserProtocol = Depends(_require_superuser),
):
    """List admin users (superuser only)."""
    templates = request.app.state.admin_jinja_env
    session = get_db_session(request)

    result = await session.execute(select(AdminUser).order_by(AdminUser.id))
    users = list(result.scalars().all())

    return templates.TemplateResponse(
        request,
        "pages/users/list.html",
        await inject_sidebar_context(
            request,
            {
                "users": users,
            },
        ),
    )


@router.get("/users/create", response_class=HTMLResponse)
async def user_create_view(
    request: Request,
    _: AdminUserProtocol = Depends(_require_superuser),
):
    """Show user create form."""
    templates = request.app.state.admin_jinja_env
    session = get_db_session(request)

    result = await session.execute(select(AdminRole).order_by(AdminRole.name))
    roles = list(result.scalars().all())

    return templates.TemplateResponse(
        request,
        "pages/users/form.html",
        await inject_sidebar_context(
            request,
            {
                "user": None,
                "roles": roles,
            },
        ),
    )


@router.post("/users/create")
async def user_create_post(
    request: Request,
    _: AdminUserProtocol = Depends(_require_superuser),
    _csrf: bool = Depends(require_csrf_token),
):
    """Handle user creation."""
    from fastapi_console.auth.backend import pwd_context
    from fastapi_console.auth.password import validate_password_strength

    session = get_db_session(request)
    form = await request.form()

    email = form.get("email", "").strip()
    password = form.get("password", "")
    full_name = form.get("full_name", "").strip()
    role_id = form.get("role_id")
    is_superuser = form.get("is_superuser") == "on"

    if not email:
        raise HTTPException(status_code=400, detail="Email is required.")

    existing = await session.execute(
        select(AdminUser).where(AdminUser.email == email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already exists.")

    password_errors = validate_password_strength(password)
    if password_errors:
        templates = request.app.state.admin_jinja_env
        result = await session.execute(
            select(AdminRole).order_by(AdminRole.name)
        )
        roles = list(result.scalars().all())
        return templates.TemplateResponse(
            request,
            "pages/users/form.html",
            await inject_sidebar_context(
                request,
                {
                    "user": None,
                    "roles": roles,
                    "error": password_errors[0],
                },
            ),
        )

    user = AdminUser(
        email=email,
        hashed_password=pwd_context.hash(password),
        full_name=full_name,
        role_id=int(role_id) if role_id else None,
        is_superuser=is_superuser,
    )
    session.add(user)
    await session.commit()

    return RedirectResponse(url="/admin/users", status_code=302)


@router.get("/users/{user_id}", response_class=HTMLResponse)
async def user_edit_view(
    request: Request,
    user_id: int,
    _: AdminUserProtocol = Depends(_require_superuser),
):
    """Show user edit form."""
    templates = request.app.state.admin_jinja_env
    session = get_db_session(request)

    user = await session.get(AdminUser, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    result = await session.execute(select(AdminRole).order_by(AdminRole.name))
    roles = list(result.scalars().all())

    return templates.TemplateResponse(
        request,
        "pages/users/form.html",
        await inject_sidebar_context(
            request,
            {
                "user": user,
                "roles": roles,
            },
        ),
    )


@router.post("/users/{user_id}")
async def user_edit_post(
    request: Request,
    user_id: int,
    current_user: AdminUserProtocol = Depends(_require_superuser),
    _csrf: bool = Depends(require_csrf_token),
):
    """Handle user edit."""
    from fastapi_console.auth.backend import pwd_context
    from fastapi_console.auth.password import validate_password_strength

    session = get_db_session(request)
    user = await session.get(AdminUser, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    form = await request.form()
    email = form.get("email", "").strip()
    password = form.get("password", "")
    full_name = form.get("full_name", "").strip()
    role_id = form.get("role_id")
    is_superuser = form.get("is_superuser") == "on"
    is_active = form.get("is_active") != "off"

    if email:
        user.email = email
    user.full_name = full_name
    user.role_id = int(role_id) if role_id else None

    # Prevent superuser from deactivating themselves
    if user.id == current_user.id and not is_active:
        raise HTTPException(
            status_code=400, detail="Cannot deactivate your own account."
        )

    if user.id == current_user.id and not is_superuser:
        raise HTTPException(
            status_code=400,
            detail="Cannot remove superuser from your own account.",
        )

    user.is_superuser = is_superuser
    user.is_active = is_active

    if password:
        password_errors = validate_password_strength(password)
        if password_errors:
            templates = request.app.state.admin_jinja_env
            result = await session.execute(
                select(AdminRole).order_by(AdminRole.name)
            )
            roles = list(result.scalars().all())
            return templates.TemplateResponse(
                request,
                "pages/users/form.html",
                await inject_sidebar_context(
                    request,
                    {
                        "user": user,
                        "roles": roles,
                        "error": password_errors[0],
                    },
                ),
            )
        user.hashed_password = pwd_context.hash(password)

    await session.commit()
    return RedirectResponse(url="/admin/users", status_code=302)


@router.post("/users/{user_id}/delete")
async def user_delete_post(
    request: Request,
    user_id: int,
    current_user: AdminUserProtocol = Depends(_require_superuser),
    _csrf: bool = Depends(require_csrf_token),
):
    """Soft-delete user (set is_active=False)."""
    session = get_db_session(request)
    user = await session.get(AdminUser, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    if user.id == current_user.id:
        raise HTTPException(
            status_code=400, detail="Cannot deactivate your own account."
        )

    user.is_active = False
    await session.commit()

    return RedirectResponse(url="/admin/users", status_code=302)
