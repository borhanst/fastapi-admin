"""Sidebar context helper for template views."""

from __future__ import annotations

from typing import Any

from fastapi import Request


async def inject_sidebar_context(request: Request, context: dict[str, Any]) -> dict[str, Any]:
    """Inject nav_groups + permissions_map into a template context dict."""
    admin_instance: Any = request.app.state.admin
    if hasattr(admin_instance, "build_sidebar_context"):
        user = getattr(request.state, "admin_user", None)

        snapshot = getattr(request.state, "admin_user_snapshot", None)
        is_superuser = (
            bool(snapshot.get("is_superuser", False))
            if snapshot
            else bool(getattr(user, "is_superuser", False))
        ) if user else False

        permissions_map: dict = {}
        if user and not is_superuser:
            role_id = (
                snapshot.get("role_id")
                if snapshot
                else getattr(user, "role_id", None)
            )
            if role_id is not None:
                try:
                    from sqlalchemy import select

                    from fastapi_console.auth.models import AdminPermission
                    from fastapi_console.db import get_db_session
                    from fastapi_console.types import PermissionSet

                    session = get_db_session(request)
                    result = await session.execute(
                        select(AdminPermission).where(
                            AdminPermission.role_id == role_id
                        )
                    )
                    rows = result.scalars().all()
                    for perm in rows:
                        permissions_map[perm.table_name] = PermissionSet(
                            can_view=perm.can_view,
                            can_create=perm.can_create,
                            can_edit=perm.can_edit,
                            can_delete=perm.can_delete,
                        )
                except Exception:
                    pass

        context.update(
            admin_instance.build_sidebar_context(
                request, user=user, permissions_map=permissions_map
            )
        )
    return context
