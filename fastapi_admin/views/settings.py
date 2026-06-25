"""Admin settings routes — theme builder."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from fastapi_admin.auth.dependencies import get_current_admin_user

router = APIRouter()


@router.get("/settings/theme", response_class=HTMLResponse)
async def theme_settings(
    request: Request,
    current_user: Any = Depends(get_current_admin_user),
):
    """Render theme builder page."""
    templates = request.app.state.admin_jinja_env
    context: dict[str, Any] = {
        "request": request,
        "title": "Theme Settings",
        "admin_config": request.app.state.admin_config,
    }
    admin_instance = request.app.state.admin
    if hasattr(admin_instance, "build_sidebar_context"):
        context.update(admin_instance.build_sidebar_context(request, user=current_user))
    template = templates.get_template("pages/settings/theme.html")
    html = template.render(**context)
    return HTMLResponse(content=html)
