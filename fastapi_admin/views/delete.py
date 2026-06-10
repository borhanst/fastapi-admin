"""Delete handler factory for registered models."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse

from fastapi_admin.flash import add_flash
from fastapi_admin.registry import RegisteredModel


def delete_factory(registered: RegisteredModel):
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
