"""Bulk action handler factory for registered models."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse

from fastapi_console.flash import add_flash
from fastapi_console.registry import RegisteredModel


def bulk_factory(registered: RegisteredModel):
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
            add_flash(request, "success", f"{len(ids)} {registered.verbose_name_plural} deleted.")
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
